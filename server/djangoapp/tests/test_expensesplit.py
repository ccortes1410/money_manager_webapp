"""
Tests for the ExpenseSplit model.

There is no dedicated ExpenseSplit endpoint -- splits are only ever
created/recalculated as a side effect of the add_expense / update_expense
endpoints (see test_sharedexpense.py's SharedExpenseAPITests), so there is
no separate APITests class here.
"""
from decimal import Decimal

from django.db import IntegrityError, transaction

from djangoapp.models.models import ExpenseSplit

from .test_base import BaseTestCase


class ExpenseSplitModelTests(BaseTestCase):
    def test_create_split_usual(self):
        split = self.create_expense_split()
        self.assertFalse(split.is_settled)

    def test_str_representation_pending(self):
        split = self.create_expense_split()
        self.assertIn('Pending', str(split))

    def test_str_representation_settled(self):
        split = self.create_expense_split()
        split.settle()
        self.assertIn('Settled', str(split))

    def test_unique_together_expense_and_user(self):
        expense = self.create_shared_expense()
        ExpenseSplit.objects.create(shared_expense=expense, user=self.user2, amount_owed=Decimal('10'))
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ExpenseSplit.objects.create(shared_expense=expense, user=self.user2, amount_owed=Decimal('20'))

    def test_same_user_different_expense_allowed(self):
        expense1 = self.create_shared_expense()
        expense2 = self.create_shared_expense(shared_budget=expense1.shared_budget)
        ExpenseSplit.objects.create(shared_expense=expense1, user=self.user2, amount_owed=Decimal('10'))
        split2 = ExpenseSplit.objects.create(shared_expense=expense2, user=self.user2, amount_owed=Decimal('15'))
        self.assertIsNotNone(split2.id)

    def test_settle_sets_flag_and_timestamp(self):
        split = self.create_expense_split()
        self.assertIsNone(split.settled_at)
        split.settle()
        self.assertTrue(split.is_settled)
        self.assertIsNotNone(split.settled_at)