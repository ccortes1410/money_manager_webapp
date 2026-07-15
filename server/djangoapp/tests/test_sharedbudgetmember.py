"""
Tests for the SharedBudgetMember model and its API endpoints.
"""

import json
from decimal import Decimal

from django.urls import reverse

from djangoapp.models.models import SharedBudgetMember

from .test_base import BaseTestCase


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
        self.budget = self.create_shared_budget()
        SharedBudgetMember.objects.create(shared_budget=self.budget, user=self.user1, role='owner')
        self.member2 = SharedBudgetMember.objects.create(shared_budget=self.budget, user=self.user2, role='editor')
        self.client.force_login(self.user1)

    def test_update_member_role_success(self):
        response = self.client.patch(
            reverse('djangoapp:update_member_role', kwargs={'budget_id': self.budget.id, 'member_id': self.member2.id}),
            data=json.dumps({'role': 'viewer'}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.member2.refresh_from_db()
        self.assertEqual(self.member2.role, 'viewer')
    
    def test_update_member_role_only_owner_can_change_roles(self):
        self.client.force_login(self.user2)
        response = self.client.patch(
            reverse('djangoapp:update_member_role', kwargs={'budget_id': self.budget.id, 'member_id': self.member2.id}),
            data=json.dumps({'role': 'viewer'}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_leave_budget_removes_membership(self):
        self.client.force_login(self.user2)
        response = self.client.post(reverse('djangoapp:leave_budget', kwargs={'budget_id': self.budget.id}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(SharedBudgetMember.objects.filter(shared_budget=self.budget, user=self.user2).exists())

    def test_leave_budget_owner_cannot_leave_with_other_members(self):
        response = self.client.post(reverse('djangoapp:leave_budget', kwargs={'budget_id': self.budget.id}))
        self.assertEqual(response.status_code, 400)

    def test_leave_budget_owner_leaving_as_last_member_deletes_budget(self):
        self.member2.delete()
        response = self.client.post(reverse('djangoapp:leave_budget', kwargs={'budget_id': self.budget.id}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(SharedBudgetMember.objects.filter(shared_budget_id=self.budget.id).exists())

    def test_remove_member_success(self):
        response = self.client.delete(
            reverse('djangoapp:remove_member', kwargs={'budget_id': self.budget.id, 'member_id': self.member2.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(SharedBudgetMember.objects.filter(id=self.member2.id).exists())

    def test_remove_member_cannot_remove_self(self):
        owner_member = SharedBudgetMember.objects.get(shared_budget=self.budget, user=self.user1)
        response = self.client.delete(
            reverse('djangoapp:remove_member', kwargs={'budget_id': self.budget.id, 'member':owner_member.id})
        )
        self.assertEqual(response.status_code, 400)

    def test_remove_member_requires_owner(self):
        self.client.force_login(self.user2)
        owner_member = SharedBudgetMember.objects.get(shared_budget=self.budget, user=self.user1)
        response = self.client.delete(
            reverse('djangoapp:remove_member', kwargs={'budget_id': self.budget.id, 'member_id': owner_member.id})
        )
        self.assertEqual(response.status_code, 403)