"""
Test for the SharedBudget model and its API endpoints.
"""
import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from djangoapp.models.models import SharedBudget, SharedBudgetMember, SharedExpense

from .test_base import BaseTestCase
from .test_api_backend import TestApiBackend
from unittest.mock import patch


class SharedBudgetModelTests(BaseTestCase):
    def test_create_shared_budget_usual(self):
        budget = self.create_shared_budget()
        self.assertTrue(budget.is_active)
        self.assertEqual(budget.default_split_type, 'equal')
    
    def test_str_representation(self):
        budget = self.create_shared_budget()
        self.assertEqual(str(budget), f"{budget.name} (${budget.total_amount})")

    def test_get_total_spent_with_no_expenses(self):
        budget = self.create_shared_budget()
        self.assertEqual(budget.get_total_spent(), 0)

    def test_get_total_spent_and_remaining_with_expenses(self):
        budget = self.create_shared_budget()
        SharedExpense.objects.create(
            shared_budget=budget, description='Groceris', amount=Decimal('0.10'),
            paid_by=self.user1, date=self.today, created_by=self.user1
        )
        self.assertEqual(budget.get_total_spent(), Decimal('0.10'))
        self.assertEqual(budget.get_remaining(), budget.total_amount - Decimal('0.10'))

    def test_get_progress_percentage_with_zero_total_amount(self):
        budget = self.create_shared_budget()
        budget.total_amount = 0
        self.assertEqual(budget.get_progress_percentage(), 0)

    def test_get_member_count_and_get_members(self):
        budget = self.create_shared_budget()
        self.create_shared_budget_member(shared_budget=budget, user=self.user2)
        self.assertEqual(budget.get_member_count(), 1)
        self.assertIn(self.user2, budget.get_members())

    def test_is_member_and_get_member_role(self):
        budget = self.create_shared_budget()
        self.create_shared_budget_member(shared_budget=budget, user=self.user2)
        self.assertTrue(budget.is_member(self.user2))
        self.assertFalse(budget.is_member(self.user3))
        self.assertEqual(budget.get_member_role(self.user2), 'owner')
        self.assertIsNone(budget.get_member_role(self.user3))

    def test_can_edit_and_can_delete_by_role(self):
        budget = self.create_shared_budget()
        SharedBudgetMember.objects.create(shared_budget=budget, user=self.user1, role='owner')
        SharedBudgetMember.objects.create(shared_budget=budget, user=self.user2, role='editor')
        SharedBudgetMember.objects.create(shared_budget=budget, user=self.user3, role='viewer')

        self.assertTrue(budget.can_edit(self.user1))
        self.assertTrue(budget.can_edit(self.user2))
        self.assertFalse(budget.can_edit(self.user3))

        self.assertTrue(budget.can_delete(self.user1))
        self.assertFalse(budget.can_delete(self.user2))
        self.assertFalse(budget.can_delete(self.user3))

    def test_can_edit_and_can_delete_for_non_member(self):
        budget = self.create_shared_budget()
        outsider = User.objects.create_user(username='outsider', password='pw')
        self.assertFalse(budget.can_edit(outsider))
        self.assertFalse(budget.can_delete(outsider))


class SharedBudgetAPITests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user1)
        # Set up mock API backend
        self.test_api = TestApiBackend()
        self.get_patcher = patch('djangoapp.restapi.requests.get', side_effects=self.test_api.get)
        self.post_patcher = patch('djangoapp.restapi.requests.post', side_effects=self.test_api.post)
        self.patch_patcher = patch('djangoapp.restapi.requests.patch', side_effects=self.test_api.patch)
        self.delete_patcher = patch('djangoapp.restapi.requests.delete', side_effects=self.test_api.delete)
        self.get_patcher.start()
        self.post_patcher.start()
        self.patch_patcher.start()
        self.delete_patcher.start()

    def tearDown(self):
        self.get_patcher.stop()
        self.post_patcher.stop()
        self.patch_patcher.stop()
        self.delete_patcher.stop()
        super().tearDown()

    def _seed_user(self, username_suffix="", **overrides):
        """Helper to seed a user via the mock API"""
        base_data = {
            "username": f"testuser{username_suffix}",
            "email": f"testuser{username_suffix}",
            "first_name": f"Test{username_suffix}",
            "last_name": "User",
        }
        base_data.update(overrides)
        return self.test_api.seed("users", base_data)

    def _seed_shared_budget(self, **overrides):
        """Helper to seed a shared budget via the mock API"""
        base_data = {
            "name": "Test Budget",
            "description": "Test Description",
            "total_amount": "1000.00",
            "category": "Test Category",
            "created_by": self.user1.id,
            "start_date": self.today.isoformat(),
            "end_date": (self.today + timezone.timedelta(days=30)).isoformat(),
            "default_split_type": "equal",
            "is_active": True,
        }
        base_data.update(overrides)
        return self.test_api.seed("shared-budgets", base_data)

    def _seed_shared_budget_member(self, **overrides):
        """Helper to seed a shared budget member via the mock API"""
        base_data = {
            "shared_budget": 1, # Will be updated after budget creation
            "user_id": self.user1.id,
            "role": "owner",
            "contribution_percentage": "100.00",
        }
        base_data.update(overrides)
        return self.test_api.seed("shared-budget-members", base_data)

    def test_get_shared_budgets_requires_auth(self):
        self.client.logout()
        response = self.client.get(reverse('djangoapp:get_shared_budgets'))
        self.assertEqual(response.status_code, 401)

    def test_get_shared_budgets_empty_list_succeeds(self):
        response = self.client.get(reverse('djangoapp:get_shared_budgets'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['total_count'], 0)

    def test_create_shared_budget_endpoint_success(self):
        # Seed users for invites
        self._seed_user("2")
        self._seed_user("3")

        payload = {
            'name': 'Vacations',
            'total_amount': 0.5,
            'period_start': self.today.isoformat(),
            'period_end': (self.today + timezone.timedelta(days=30)).isoformat(),
            # Note: Using correct field names period_start/period_end
        }
        response = self.client.post(
            reverse('djangoapp:create_shared_budget'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

        # Check that the budget was added to the mock API
        budgets = self.test_api.resources.get("shared-budgets", [])
        self.assertEqual(len(budgets), 1)
        self.assertEqual(budgets[0]['name'], 'Vacations')
        self.assertEqual(float(budgets[0]['total_amount']), 0.5)

    def test_get_shared_budget_detail_success(self):
        # Seed budget
        budget = self._seed_shared_budget()

        response = self.client.get(
            reverse('djangoapp:get_shared_budget_detail', kwargs={'budget_id': budget['id']})
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['id'], budget['id'])
        self.assertEqual(data['name'], budget['name'])

    def test_update_shared_budget_endpoint_success(self):
        # Seed budget
        budget = self._seed_shared_budget()

        # Ssed member (creator as owner)
        member_data = self._seed_shared_budget_member(shared_budget=budget['id'])

        response = self.client.patch(
            reverse('djangoapp:update_shared_budget', kwargs={'budget_id': budget['id']}),
            data=json.dumps({'name': 'Updated Budget Name'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Check that the budget was updated in the mock API
        updated_budget = next((b for b in self.test_api.resources["shared-budgets"] if b['id'] == budget['id']), None)
        self.assertIsNotNone(updated_budget)
        self.assertEqual(updated_budget['name'], 'Updated Budget Name')

        def test_delete_shared_budget_endpoint_success(self):
            # Seed budget
            budget = self._seed_shared_budget()

            # Seed member (creator as owner)
            member_data = self._seed_shared_budget_member(shared_budget=budget['id'])

            response = self.client.delete(
                reverse('djangoapp:delete_shared_budget', kwargs={'budget_id': budget['id']}),
                content_type='appication/json'
            )
            self.assertEqual(response.status_code, 200)

            # Check that the budget was deleted from the mock API
            budgets = self.test_api.resources.get("shared-budgets", [])
            self.assertEqual(len(budgets), 0)