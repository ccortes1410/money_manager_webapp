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


class SharedBudgetModelTests(BaseTestCase):
    def test_create_shared_budget_usual(self):
        budget = self.create_shared_budget()
        self.assertTrue(budget.is_active)
        self.assertEqual(budget.default_split_type, 'equal')
    
    def test_str_representation(self):
        budget = self.create_shared_budget()
        self.assertEqual(str(budget), f"{budget.name} (${budget.total_amount})")

    # def test_total_amount_field_is_too_restrictive_bug(self):
    #     """
    #     total_amount = DecimalField(max_digits=12, decimal_places=12)
    #     leaves zero digits for the integer part, so amount >= 1 fail validation.
    #     Likely meant to be decimal_places=2.
    #     """
    #     budget = SharedBudget(
    #         name='Big Budget', total_amount=Decimal('1000'),
    #         created_by=self.user1, period_start=self.today,
    #         period_end=self.today + timezone.timedelta(days=30),
    #     )
    #     with self.assertRaises(Exception):
    #         budget.full_clean()

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

    def test_get_shared_budgets_requires_auth(self):
        self.client.logout()
        response = self.client.get(reverse('djangoapp:get_shared_budgets'))
        self.assertEqual(response.status_code, 401)

    def test_get_shared_budgets_empty_list_succeeds(self):
        response = self.client.get(reverse('djangoapp:get_shared_budgets'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['total_count'], 0)

    # def test_get_shared_budgets_with_a_budget_raises_serialize_bug(self):
    #     budget = self.create_shared_budget()
    #     SharedBudgetMember.objects.create(shared_budget=budget, user=self.user1, role='owner')
    #     with self.assertRaises(AttributeError):
    #         self.client.get(reverse('djangoapp:get_shared_budgets'))

    def test_create_shared_budget_endpoint_fails_bug(self):
        """
        create_shared_budget() calls
        SharedBudget.objects.create(start_date=..., end_date=..., ...) but
        the model's actual fields are 'period_start' / 'period_end', not
        'start_date' / 'end_date'. Django raises a TypeError for the
        invalid keyword arguments, which the view's try/except catches and
        turns into a 500 response -- so no budget is ever created.
        """
        payload = {
            'name': 'Vacations',
            'total_amount': 0.5,
            'start_date': self.today.isoformat(),
            'end_date': (self.today + timezone.timedelta(days=30)).isoformat(),
        }
        response = self.client.post(
            reverse('djangoapp:create_shared_budget'), data=json.dumps(payload), content_type='application/json'
        )
        self.assertEqual(response.status_code, 500)
        self.assertFalse(SharedBudget.objects.filter(name='Vacations').exists())

    # def test_get_shared_budget_detail_raises_queryset_bug(self):
    #     budget = self.create_shared_budget()
    #     with self.assertRaises(AttributeError):
    #         self.client.get(
    #             reverse('djangoapp:get_shared_budget_detail', kwargs={'budget_id': budget.id})
    #         )
    
    # def test_update_shared_budget_raises_json_load_bug(self):
    #     budget = self.create_shared_budget()
    #     with self.assertRaises(AttributeError):
    #         self.client.patch(
    #             reverse('djangoapp:update_shared_budget', kwargs={'budget_id': budget.id}),
    #             data=json.dumps({'name': 'New Name'}), content_type='application/json'
    #         )

    # def test_delete_shared_budget_raises_queryset_bug(self):
    #     budget = self.create_shared_budget()
    #     with self.assertRaises(AttributeError):
    #         self.client.delete(reverse('djangoapp:delete_shared_budget', kwargs={'budget_id': budget.id}))