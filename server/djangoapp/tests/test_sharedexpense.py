""""
Tests for the SharedExpense model and its API endpoints.
"""
import json
from decimal import Decimal

from django.urls import reverse

from djangoapp.models.models import SharedBudgetMember, SharedExpense

from .test_base import BaseTestCase


class SharedExpenseModelTests(BaseTestCase):
    def test_create_expense_usual(self):
        expense = self.create_shared_expense()
        self.assertEqual(expense.description, 'Test Shared Expense')

    def test_str_representation(self):
        expense = self.create_shared_expense()
        expected = f"{expense.description} - ${expense.amount} by {expense.paid_by.username}"
        self.assertEqual(str(expense), expected)

    def test_create_equal_splits_with_members(self):
        budget = self.create_shared_budget()
        SharedBudgetMember.objects.create(shared_budget=budget, user=self.user1, role='owner')
        SharedBudgetMember.objects.create(shared_budget=budget, user=self.user2, role='editor')

        expense = SharedExpense.objects.create(
            shared_budget=budget, description='Split Test', amount=Decimal('100'),
            paid_by=self.user1, date=self.today, created_by=self.user1
        )
        expense.create_equal_splits()

        splits = expense.splits.all()
        self.assertEqual(splits.count(), 2)
        for split in splits:
            self.assertEqual(split.amount_owed, Decimal('50'))

    def test_create_equal_splits_with_no_members_does_nothing(self):
        budget = self.create_shared_budget()
        expense = SharedExpense.objects.create(
            shared_budget=budget, description='No Members', amount=Decimal('50'),
            paid_by=self.user1, date=self.today, created_by=self.user1
        )
        expense.create_equal_splits()
        self.assertEqual(expense.splits.count(), 0)

    def test_create_percentage_splits(self):
        budget = self.create_shared_budget()
        SharedBudgetMember.objects.create(
            shared_budget=budget, user=self.user1, role='owner', contribution_percentage=Decimal('70')
        )
        SharedBudgetMember.objects.create(
            shared_budget=budget, user=self.user2, role='editor', contribution_percentage=Decimal('30')
        )

        expense = SharedExpense.objects.create(
            shared_budget=budget, description='Percentage Test', amount=Decimal('100'),
            paid_by=self.user1, date=self.today, created_by=self.user1
        )
        expense.create_percentage_splits()

        split1 = expense.splits.get(user=self.user1)
        split2 = expense.splits.get(user=self.user2)
        self.assertEqual(split1.amount_owed, Decimal('70'))
        self.assertEqual(split2.amount_owed, Decimal('30'))

    # def test_create_custom_splits_bug(self):
    #     """
    #     create_custom_splits() calls ExpenseSplit.objects.create(expense=self, ...)
    #     but the FK field is named 'shared_expense', not 'expense'.
    #     """
    #     expense = self.create_shared_expense()
    #     with self.assertRaises(TypeError):
    #         expense.create_custom_splits([{'user_id': self.user1.id, 'amount': 25.0}])

    def test_create_custom_splits_creates_one_split_per_entry(self):
        expense = self.create_shared_expense()
        splits = expense.create_custom_splits([
            {'user_id': self.user1.id, 'amount': 60.0},
            {'user_id': self.user2.id, 'amount': 40.0},
        ])

        self.assertEqual(len(splits), 2)
        self.assertEqual(expense.splits.count(), 2)

        split1 = expense.splits.get(user=self.user1)
        split2 = expense.splits.get(user=self.user2)
        self.assertEqual(split1.amount_owed, Decimal('60.0'))
        self.assertEqual(split2.amount_owed, Decimal('40.0'))

    def test_create_custom_splits_total_matches_expense_amount(self):
        expense = self.create_shared_expense()
        splits = expense.create_custom_splits([
            {'user_id': self.user1.id, 'amount': 60.0},
            {'user_id': self.user2.id, 'amount': 40.0},
        ])
        total_owed = sum(s.amount_owed for s in splits)
        self.assertEqual(total_owed, expense.amount)

    def test_create_custom_splits_returns_created_splits(self):
        expense = self.create_shared_expense()
        splits = expense.create_custom_splits([{'user_id': self.user1.id, 'amount': 25.0}])
        self.assertEqual(len(splits), 1)
        self.assertEqual(splits[0].user, self.user1)
        self.assertEqual(splits[0].shared_expense, expense)

class SharedExpenseAPITests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.budget = self.create_shared_budget()
        SharedBudgetMember.objects.create(shared_budget=self.budget, user=self.user1, role='owner')
        SharedBudgetMember.objects.create(shared_budget=self.budget, user=self.user2, role='editor')
        self.client.force_login(self.user1)

    def test_add_expense_success_default_equal_splits(self):
        payload = {
            'description': 'Groceries',
            'amount': 0.10,
            'date': self.today.isoformat(),
            'category': 'Food',
        }
        response = self.client.post(
            reverse('djangoapp:add_expense', kwargs={'budget_id': self.budget.id}),
            data=json.dumps(payload), content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        expense = SharedExpense.objects.get(shared_budget=self.budget, description='Groceries')
        self.assertEqual(expense.splits.count(), 2)

    def test_add_expense_requires_edit_permission(self):
        outsider = self.user3
        self.client.force_login(outsider)
        payload = {'description': 'Groceries', 'amount': 10, 'date': self.today.isoformat()}
        response = self.client.post(
            reverse('djangoapp:add_expense', kwargs={'budget_id': self.budget.id}),
            data=json.dumps(payload), content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_add_expense_missing_description(self):
        response = self.client.post(
            reverse('djangoapp:add_expense', kwargs={'budget_id': self.budget.id}),
            data=json.dumps({'amount': 10}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_add_expense_custom_split_type_uses_custom_amounts(self):
        payload = {
            'description': 'Custom Split',
            'amount': 100,
            'date': self.today.isoformat(),
            'split_type': 'custom',
            'splits': [
                {
                    'user_id': self.user1.id,
                    'amount': 80
                },
                {
                    'user_id': self.user2.id,
                    'amount': 20
                }
            ]
        }
        response = self.client.post(
            reverse('djangoapp:add_expense', kwargs={'budget_id': self.budget.id}),
            data=json.dumps(payload), content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        expense = SharedExpense.objects.get(shared_budget=self.budget, description='Custom Split')
        self.assertEqual(expense.splits.get(user=self.user1).amount_owed, Decimal('80'))
        self.assertEqual(expense.splits.get(user=self.user2).amount_owed, Decimal('20'))

    def test_update_expense_changes_amount_and_recalculates_splits(self):
        expense = SharedExpense.objects.create(
            shared_budget=self.budget, description='Dinner', amount=Decimal('0.10'),
            paid_by=self.user1, date=self.today, created_by=self.user1
        )
        expense.create_equal_splits()
        response = self.client.patch(
            reverse('djangoapp:update_expense', kwargs={'budget_id': self.budget.id, 'expense_id': expense.id}),
            data=json.dumps({'amount': 0.20}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        expense.refresh_from_db()
        self.assertEqual(expense.amount, Decimal('0.20'))
        for split in expense.splits.all():
            self.assertEqual(split.amount_owed, Decimal('0.10'))

    def test_delete_expense_removes_it(self):
        expense = self.create_shared_expense(shared_budget=self.budget)
        response = self.client.delete(
            reverse('djangoapp:delete_expense', kwargs={'budget_id': self.budget.id, 'expense_id': expense.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(SharedExpense.objects.filter(id=expense.id).exists())

    def test_get_budget_expenses_returns_all(self):
        self.create_shared_expense(shared_budget=self.budget)
        response = self.client.get(reverse('djangoapp:get_budget_expenses', kwargs={'budget_id': self.budget.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)

    def test_get_budget_expenses_paid_by_filter_bug(self):
        self.create_shared_expense(shared_budget=self.budget)
        with self.assertRaises(AttributeError):
            self.client.get(
                reverse('djangoapp:get_budget_expenses', kwargs={'budget_id': self.budget.id}),
                {'paid_by': self.user1.id}
            )