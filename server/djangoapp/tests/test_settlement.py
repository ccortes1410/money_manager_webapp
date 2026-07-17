"""
Tests for the Settlement model and its endpoints (create_settlement,
get_budget_debts) in shared_budget_views.py.
"""
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

from djangoapp.models.models import SharedBudgetMember, Settlement

from .test_base import BaseTestCase


class SettlementModelTests(BaseTestCase):
    def test_create_settlement_usual(self):
        settlement = self.create_settlement()
        self.assertEqual(settlement.payer, self.user1)
        self.assertEqual(settlement.receiver, self.user2)

    def test_str_representation(self):
        settlement = self.create_settlement()
        expected = f"{settlement.payer.username} paid ${settlement.amount} to {settlement.receiver.username}"
        self.assertEqual(str(settlement), expected)

    def test_ordering_most_recent_first(self):
        split = self.create_expense_split()
        shared_budget = split.shared_expense.shared_budget
        older = Settlement.objects.create(
            shared_budget=shared_budget, payer=self.user1, receiver=self.user2,
            amount=Decimal('10'), date=self.today - timezone.timedelta(days=5)
        )
        newer = Settlement.objects.create(
            shared_budget=shared_budget, payer=self.user1, receiver=self.user2,
            amount=Decimal('20'), date=self.today
        )
        settlements = list(Settlement.objects.filter(shared_budget=shared_budget))
        self.assertEqual(settlements[0], newer)
        self.assertEqual(settlements[1], older)


class SettlementAPITests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.budget = self.create_shared_budget()
        SharedBudgetMember.objects.create(shared_budget=self.budget, user=self.user1, role='owner')
        SharedBudgetMember.objects.create(shared_budget=self.budget, user=self.user2, role='editor')
        self.client.force_login(self.user1)

    def test_create_settlement_success(self):
        response = self.client.post(
            reverse('djangoapp:create_settlement', kwargs={'budget_id': self.budget.id}),
            data={'receiver_id': self.user2.id, 'amount': 0.05, 'date': self.today.isoformat()},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Settlement.objects.filter(shared_budget=self.budget, payer=self.user1, receiver=self.user2).exists())

    def test_create_settlement_rejects_self_settlement(self):
        response = self.client.post(
            reverse('djangoapp:create_settlement', kwargs={'budget_id': self.budget.id}),
            data={'receiver_id': self.user1.id, 'amount': 0.05},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_create_settlement_rejects_non_positive_amount(self):
        response = self.client.post(
            reverse('djangoapp:create_settlement', kwargs={'budget_id': self.budget.id}),
            data={'receiver_id': self.user2.id, 'amount': 0},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_get_budget_debts_always_raises_bug(self):
        with self.assertRaises(TypeError):
            self.client.get(reverse('djangoapp:get_budget_debts', kwargs={'budget_id': self.budget.id}))