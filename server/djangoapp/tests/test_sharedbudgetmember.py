"""
Tests for the SharedBudgetMember model and its API endpoints.
"""
import json
from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone

from djangoapp.models.models import SharedBudgetMember
from djangoapp.models.friendship import Friendship

from .test_base import BaseTestCase
from .test_api_backend import TestApiBackend


class SharedBudgetMemberModelTests(BaseTestCase):
    def test_create_member_usual(self):
        member = self.create_shared_budget_member()
        self.assertEqual(member.role, 'owner')

    def test_str_representation(self):
        member = self.create_shared_budget_member()
        expected = f"{member.user.username} - {member.shared_budget.name} ({member.role})"
        self.assertEqual(str(member), expected)

    def test_unique_together_budget_and_user(self):
        from django.db import IntegrityError, transaction
        budget = self.create_shared_budget()
        SharedBudgetMember.objects.create(shared_budget=budget, user=self.user2, role='editor')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SharedBudgetMember.objects.create(shared_budget=budget, user=self.user2, role='viewer')

    def test_get_toital_paid_owed_and_balance(self):
        from djangoapp.models.models import SharedExpense, ExpenseSplit
        budget = self.create_shared_budget()
        member = SharedBudgetMember.objects.create(shared_budget=budget, user=self.user2, role='editor')

        expense = SharedExpense.objects.create(
            shared_budget=budget, description='Dinner', amount=Decimal('500'),
            paid_by=self.user2, date=self.today, created_by=self.user2
        )
        ExpenseSplit.objects.create(
            shared_expense=expense, user=self.user2, amount_owed=Decimal('250'), is_settled=False
        )

        self.assertEqual(member.get_total_paid(), Decimal('500'))
        self.assertEqual(member.get_total_owed(), Decimal('250'))
        self.assertEqual(member.get_balance(), Decimal('250'))

    def test_get_total_owed_ignores_settled_splits(self):
        from djangoapp.models.models import SharedExpense, ExpenseSplit
        budget = self.create_shared_budget()
        member = SharedBudgetMember.objects.create(shared_budget=budget, user=self.user2, role='editor')
        expense = SharedExpense.objects.create(
            shared_budget=budget, description='Coffee', amount=Decimal('500'),
            paid_by=self.user1, date=self.today, created_by=self.user1
        )
        ExpenseSplit.objects.create(
            shared_expense=expense, user=self.user2, amount_owed=Decimal('500'), is_settled=True
        )
        self.assertEqual(member.get_total_owed(), 0)


class SharedBudgetMemberAPITests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user1)
        # Set up mock API backend
        self.test_api = TestApiBackend()
        self.get_patcher = patch('djangoapp.restapi.requests.get', side_effect=self.test_api.get)
        self.post_patcher = patch('djangoapp.restapi.requests.post', side_effect=self.test_api.post)
        self.patch_patcher = patch('djangoapp.restapi.requests.patch', side_effect=self.test_api.patch)
        self.delete_patcher = patch('djangoapp.restapi.requests.delete', side_effect=self.test_api.delete)
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
            "email": f"testuser{username_suffix}@example.com",
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
            "period_start": self.today.isoformat(),
            "period_end": (self.today + timezone.timedelta(days=30)).isoformat(),
            "default_split_type": "equal",
            "is_active": True,
        }
        base_data.update(overrides)
        return self.test_api.seed("shared-budgets", base_data)

    def _seed_shared_budget_member(self, **overrides):
        """Helper to seed a shared budget member via the mock API"""
        base_data = {
            "shared_budget": None,  # Will be set by caller
            "user_id": self.user1.id,
            "role": "owner",
            "contribution_percentage": "100.00",
            "joined_at": self.today.isoformat(),
        }
        base_data.update(overrides)
        return self.test_api.seed("shared-budget-members", base_data)

    def test_update_member_role_success(self):
        # Seed budget
        budget = self._seed_shared_budget()
        # Seed member (creator as owner)
        member_data = self._seed_shared_budget_member(shared_budget=budget['id'], role='owner')
        # Seed another user to be made editor
        user2 = self._seed_user("2")
        # Seed member for user2
        member2_data = self._seed_shared_budget_member(
            shared_budget=budget['id'],
            user_id=user2['id'],
            role='editor'
        )

        response = self.client.patch(
            reverse('djangoapp:update_member_role', kwargs={'budget_id': budget['id'], 'member_id': member2_data['id']}),
            data=json.dumps({'role': 'viewer'}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Check that the member role was updated in the mock API
        members = self.test_api.resources["shared-budget-members"]
        updated_member = [m for m in members if m["id"] == member2_data['id']][0]
        self.assertEqual(updated_member["role"], 'viewer')

    def test_update_member_role_only_owner_can_change_roles(self):
        # Seed budget
        budget = self._seed_shared_budget()
        # Seed member (creator as owner)
        member_data = self._seed_shared_budget_member(shared_budget=budget['id'], role='owner')
        # Seed another user to be made editor
        user2 = self._seed_user("2")
        # Seed member for user2 (editor)
        member2_data = self._seed_shared_budget_member(
            shared_budget=budget['id'],
            user_id=user2['id'],
            role='editor'
        )

        # Login as user2 (not owner) and try to change role
        self.client.force_login(self.user2)
        response = self.client.patch(
            reverse('djangoapp:update_member_role', kwargs={'budget_id': budget['id'], 'member_id': member2_data['id']}),
            data=json.dumps({'role': 'viewer'}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

        # Check that the member role was NOT updated in the mock API
        members = self.test_api.resources["shared-budget-members"]
        member = [m for m in members if m["id"] == member2_data['id']][0]
        self.assertEqual(member["role"], 'editor')  # Should remain editor

    def test_leave_budget_removes_membership(self):
        # Seed budget
        budget = self._seed_shared_budget()
        # Seed member (creator as owner) - using existing Django user1
        member_data = self._seed_shared_budget_member(shared_budget=budget['id'], user_id=self.user1.id, role='owner')
        # Seed member for user2 - using existing Django user2
        member2_data = self._seed_shared_budget_member(
            shared_budget=budget['id'],
            user_id=self.user2.id,
            role='editor'
        )

        # Login as user2 and leave budget
        self.client.force_login(self.user2)
        response = self.client.post(reverse('djangoapp:leave_budget', kwargs={'budget_id': budget['id']}))
        self.assertEqual(response.status_code, 200)

        # Check that the member was removed from the mock API
        members = self.test_api.resources["shared-budget-members"]
        member_ids = [m["id"] for m in members if m["shared_budget"] == budget['id'] and m["user_id"] == self.user2.id]
        self.assertEqual(len(member_ids), 0)  # Member should be removed

    def test_leave_budget_owner_cannot_leave_with_other_members(self):
        # Seed budget
        budget = self._seed_shared_budget()
        # Seed member (creator as owner) - using existing Django user1
        member_data = self._seed_shared_budget_member(shared_budget=budget['id'], user_id=self.user1.id, role='owner')
        # Seed member for user2 - using existing Django user2
        member2_data = self._seed_shared_budget_member(
            shared_budget=budget['id'],
            user_id=self.user2.id,
            role='editor'
        )

        # Login as owner (user1) and try to leave (should fail because there are other members)
        self.client.force_login(self.user1)
        response = self.client.post(reverse('djangoapp:leave_budget', kwargs={'budget_id': budget['id']}))
        self.assertEqual(response.status_code, 400)

        # Check that the owner member still exists
        members = self.test_api.resources["shared-budget-members"]
        member_ids = [m["id"] for m in members if m["shared_budget"] == budget['id'] and m["user_id"] == self.user1.id]
        self.assertEqual(len(member_ids), 1)  # Owner should still be there

    def test_leave_budget_owner_leaving_as_last_member_deletes_budget(self):
        # Seed budget
        budget = self._seed_shared_budget()
        # Seed member (creator as owner)
        owner_member_data = self._seed_shared_budget_member(shared_budget=budget['id'], role='owner')

        # Login as owner and leave budget (should delete budget since they're the only member)
        self.client.force_login(self.user1)
        response = self.client.post(reverse('djangoapp:leave_budget', kwargs={'budget_id': budget['id']}))
        self.assertEqual(response.status_code, 200)

        # Check that the budget was deleted from the mock API
        budgets = self.test_api.resources.get("shared-budgets", [])
        budget_ids = [b["id"] for b in budgets if b["id"] == budget['id']]
        self.assertEqual(len(budget_ids), 0)  # Budget should be deleted

    def test_remove_member_success(self):
        # Seed budget
        budget = self._seed_shared_budget()
        # Seed member (creator as owner)
        owner_member_data = self._seed_shared_budget_member(shared_budget=budget['id'], role='owner')
        # Seed another user
        user2 = self._seed_user("2")
        # Seed member for user2
        member2_data = self._seed_shared_budget_member(
            shared_budget=budget['id'],
            user_id=user2['id'],
            role='editor'
        )

        # Login as owner and remove user2
        self.client.force_login(self.user1)
        response = self.client.delete(
            reverse('djangoapp:remove_member', kwargs={'budget_id': budget['id'], 'member_id': member2_data['id']})
        )
        self.assertEqual(response.status_code, 200)

        # Check that the member was removed from the mock API
        members = self.test_api.resources["shared-budget-members"]
        member_ids = [m["id"] for m in members if m["shared_budget"] == budget['id'] and m["user_id"] == user2['id']]
        self.assertEqual(len(member_ids), 0)  # Member should be removed

    def test_remove_member_cannot_remove_self(self):
        # Seed budget
        budget = self._seed_shared_budget()
        # Seed member (creator as owner)
        owner_member_data = self._seed_shared_budget_member(shared_budget=budget['id'], role='owner')
        # Seed another user
        user2 = self._seed_user("2")
        # Seed member for user2
        member2_data = self._seed_shared_budget_member(
            shared_budget=budget['id'],
            user_id=user2['id'],
            role='editor'
        )

        # Login as owner and try to remove themselves (should fail)
        self.client.force_login(self.user1)
        response = self.client.delete(
            reverse('djangoapp:remove_member', kwargs={'budget_id': budget['id'], 'member_id': owner_member_data['id']})
        )
        self.assertEqual(response.status_code, 400)

        # Check that the owner member still exists
        members = self.test_api.resources["shared-budget-members"]
        member_ids = [m["id"] for m in members if m["shared_budget"] == budget['id'] and m["user_id"] == self.user1.id]
        self.assertEqual(len(member_ids), 1)  # Owner should still be there

    def test_remove_member_requires_owner(self):
        # Seed budget
        budget = self._seed_shared_budget()
        # Seed member (creator as owner)
        owner_member_data = self._seed_shared_budget_member(shared_budget=budget['id'], role='owner')
        # Seed another user
        user2 = self._seed_user("2")
        # Seed member for user2 (editor)
        member2_data = self._seed_shared_budget_member(
            shared_budget=budget['id'],
            user_id=user2['id'],
            role='editor'
        )

        # Login as user2 (not owner) and try to remove owner
        self.client.force_login(self.user2)
        response = self.client.delete(
            reverse('djangoapp:remove_member', kwargs={'budget_id': budget['id'], 'member_id': owner_member_data['id']})
        )
        self.assertEqual(response.status_code, 403)

        # Check that the owner member still exists
        members = self.test_api.resources["shared-budget-members"]
        member_ids = [m["id"] for m in members if m["shared_budget"] == budget['id'] and m["user_id"] == self.user1.id]
        self.assertEqual(len(member_ids), 1)  # Owner should still be there