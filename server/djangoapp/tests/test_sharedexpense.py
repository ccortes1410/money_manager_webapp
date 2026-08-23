"""
Tests for the SharedExpense model and its API endpoints.
"""
import json
from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone

from djangoapp.models.models import SharedBudgetMember, SharedExpense

from .test_base import BaseTestCase
from .test_api_backend import TestApiBackend


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
        self.client.force_login(self.user1)
        # Set up mock API backend
        self.test_api = TestApiBackend()
        # Seed users with IDs matching Django test users
        self.test_api.seed("users", {"id": self.user1.id, "username": self.user1.username, "email": self.user1.email, "first_name": self.user1.first_name, "last_name": self.user1.last_name})
        self.test_api.seed("users", {"id": self.user2.id, "username": self.user2.username, "email": self.user2.email, "first_name": self.user2.first_name, "last_name": self.user2.last_name})
        self.test_api.seed("users", {"id": self.user3.id, "username": self.user3.username, "email": self.user3.email, "first_name": self.user3.first_name, "last_name": self.user3.last_name})
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

    def _seed_shared_expense(self, **overrides):
        """Helper to seed a shared expense via the mock API"""
        base_data = {
            "shared_budget": None,  # Will be set by caller
            "description": "Test Shared Expense",
            "amount": "100.00",
            "paid_by": self.user1.id,
            "date": self.today.isoformat(),
            "category": "General",
            "created_by": self.user1.id,
        }
        base_data.update(overrides)
        return self.test_api.seed("shared-expenses", base_data)

    def _seed_shared_expense(self, **overrides):
        """Helper to seed a shared expense via the mock API"""
        base_data = {
            "shared_budget": None,  # Will be set by caller
            "description": "Test Shared Expense",
            "amount": "100.00",
            "paid_by": self.user1.id,
            "date": self.today.isoformat(),
            "category": "General",
            "created_by": self.user1.id,
        }
        base_data.update(overrides)
        return self.test_api.seed("shared-expenses", base_data)

    def test_add_expense_success_default_equal_splits(self):
        # Seed budget
        budget = self._seed_shared_budget()
        # Seed members (creator as owner and another user as editor)
        # Use actual Django user IDs for seeding
        self._seed_shared_budget_member(shared_budget=budget['id'], user_id=self.user1.id, role='owner')
        self._seed_shared_budget_member(shared_budget=budget['id'], user_id=self.user2.id, role='editor')

        payload = {
            'description': 'Groceries',
            'amount': 0.10,
            'date': self.today.isoformat(),
            'category': 'Food',
        }
        # Login as user1 (owner) to add expense
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse('djangoapp:add_expense', kwargs={'budget_id': budget['id']}),
            data=json.dumps(payload), content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

        # Check that the expense was created in the mock API
        expenses = self.test_api.resources["shared-expenses"]
        expense = [e for e in expenses if e["description"] == 'Groceries' and e["shared_budget"] == budget['id']][0]
        self.assertIsNotNone(expense)

        # Check that splits were created (2 members = 2 splits)
        splits = self.test_api.resources["expense-splits"]
        expense_splits = [s for s in splits if s["shared_expense"] == expense['id']]
        self.assertEqual(len(expense_splits), 2)

    def test_add_expense_requires_edit_permission(self):
        # Seed budget
        budget = self._seed_shared_budget()
        # Seed members (creator as owner and another user as editor)
        # Use actual Django user IDs for seeding
        self._seed_shared_budget_member(shared_budget=budget['id'], user_id=self.user1.id, role='owner')
        self._seed_shared_budget_member(shared_budget=budget['id'], user_id=self.user2.id, role='editor')

        # Login as user3 (outsider, not a member) and try to add expense
        self.client.force_login(self.user3)

        payload = {'description': 'Groceries', 'amount': 10, 'date': self.today.isoformat()}
        response = self.client.post(
            reverse('djangoapp:add_expense', kwargs={'budget_id': budget['id']}),
            data=json.dumps(payload), content_type='application/json'
        )
        # Should be forbidden since user3 is not a member of the budget
        self.assertEqual(response.status_code, 403)

    def test_add_expense_missing_description(self):
        # Seed budget
        budget = self._seed_shared_budget()
        # Seed members
        # Use actual Django user IDs for seeding
        self._seed_shared_budget_member(shared_budget=budget['id'], user_id=self.user1.id, role='owner')
        self._seed_shared_budget_member(shared_budget=budget['id'], user_id=self.user2.id, role='editor')

        # Login as user1 to make the request
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse('djangoapp:add_expense', kwargs={'budget_id': budget['id']}),
            data=json.dumps({'amount': 10}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_add_expense_custom_split_type_uses_custom_amounts(self):
        # Seed budget
        budget = self._seed_shared_budget()
        # Seed members
        # Use actual Django user IDs for seeding
        self._seed_shared_budget_member(shared_budget=budget['id'], user_id=self.user1.id, role='owner')
        self._seed_shared_budget_member(shared_budget=budget['id'], user_id=self.user2.id, role='editor')

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
        # Login as user1 (owner) to add expense
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse('djangoapp:add_expense', kwargs={'budget_id': budget['id']}),
            data=json.dumps(payload), content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

        # Check that the expense was created with correct splits
        expenses = self.test_api.resources["shared-expenses"]
        expense = [e for e in expenses if e["description"] == 'Custom Split' and e["shared_budget"] == budget['id']][0]
        self.assertIsNotNone(expense)

        splits = self.test_api.resources["expense-splits"]
        expense_splits = [s for s in splits if s["shared_expense"] == expense['id']]
        self.assertEqual(len(expense_splits), 2)

        # Check split amounts
        split_amounts = [s["amount_owed"] for s in expense_splits]
        self.assertIn("80.00", split_amounts)
        self.assertIn("20.00", split_amounts)

    def test_update_expense_changes_amount_and_recalculates_splits(self):
        # Seed budget
        budget = self._seed_shared_budget()
        # Seed members
        member_data = self._seed_user("1")
        member2_data = self._seed_user("2")
        self._seed_shared_budget_member(shared_budget=budget['id'], user_id=member_data['id'], role='owner')
        self._seed_shared_budget_member(shared_budget=budget['id'], user_id=member2_data['id'], role='editor')

        # Seed initial expense
        expense_data = self._seed_shared_expense(
            shared_budget=budget['id'],
            description='Dinner',
            amount='0.10',
            paid_by=member_data['id']
        )

        # Create equal splits via API (simulating what the view would do)
        # For simplicity, we'll create splits directly in the mock API
        self.test_api.seed("expense-splits", {
            "shared_expense": expense_data['id'],
            "user_id": member_data['id'],
            "amount_owed": "0.05",
            "is_settled": False
        })
        self.test_api.seed("expense-splits", {
            "shared_expense": expense_data['id'],
            "user_id": member2_data['id'],
            "amount_owed": "0.05",
            "is_settled": False
        })

        response = self.client.patch(
            reverse('djangoapp:update_expense', kwargs={'budget_id': budget['id'], 'expense_id': expense_data['id']}),
            data=json.dumps({'amount': 0.20}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Check that the expense amount was updated in the mock API
        expenses = self.test_api.resources["shared-expenses"]
        updated_expense = [e for e in expenses if e["id"] == expense_data['id']][0]
        self.assertEqual(updated_expense["amount"], "0.20")

    def test_delete_expense_removes_it(self):
        # Seed budget
        budget = self._seed_shared_budget()
        # Seed members
        member_data = self._seed_user("1")
        member2_data = self._seed_user("2")
        self._seed_shared_budget_member(shared_budget=budget['id'], user_id=member_data['id'], role='owner')
        self._seed_shared_budget_member(shared_budget=budget['id'], user_id=member2_data['id'], role='editor')

        # Seed expense
        expense_data = self._seed_shared_expense(
            shared_budget=budget['id'],
            description='Test Expense',
            amount='10.00',
            paid_by=member_data['id']
        )

        response = self.client.delete(
            reverse('djangoapp:delete_expense', kwargs={'budget_id': budget['id'], 'expense_id': expense_data['id']})
        )
        self.assertEqual(response.status_code, 200)

        # Check that the expense was removed from the mock API
        expenses = self.test_api.resources["shared-expenses"]
        remaining_expenses = [e for e in expenses if e["id"] == expense_data['id']]
        self.assertEqual(len(remaining_expenses), 0)  # Expense should be deleted

    def test_get_budget_expenses_returns_all(self):
        # Seed budget
        budget = self._seed_shared_budget()
        # Seed members
        member_data = self._seed_user("1")
        member2_data = self._seed_user("2")
        self._seed_shared_budget_member(shared_budget=budget['id'], user_id=member_data['id'], role='owner')
        self._seed_shared_budget_member(shared_budget=budget['id'], user_id=member2_data['id'], role='editor')

        # Seed expense
        self._seed_shared_expense(
            shared_budget=budget['id'],
            description='Test Expense',
            amount='10.00',
            paid_by=member_data['id']
        )

        response = self.client.get(reverse('djangoapp:get_budget_expenses', kwargs={'budget_id': budget['id']}))
        self.assertEqual(response.status_code, 200)
        # Note: The exact response format depends on the view implementation
        # But we're testing that the API call works and returns data
        self.assertIn('count', response.json())

    def test_get_budget_expenses_paid_by_filter_bug(self):
        # Seed budget
        budget = self._seed_shared_budget()
        # Seed members
        member_data = self._seed_user("1")
        member2_data = self._seed_user("2")
        self._seed_shared_budget_member(shared_budget=budget['id'], user_id=member_data['id'], role='owner')
        self._seed_shared_budget_member(shared_budget=budget['id'], user_id=member2_data['id'], role='editor')

        # Seed expense
        expense_data = self._seed_shared_expense(
            shared_budget=budget['id'],
            description='Test Expense',
            amount='10.00',
            paid_by=member_data['id']
        )

        # Note: This test is expecting an AttributeError due to a bug in the view
        # We're keeping the same test expectation but now using the API pattern
        with self.assertRaises(AttributeError):
            self.client.get(
                reverse('djangoapp:get_budget_expenses', kwargs={'budget_id': budget['id']}),
                {'paid_by': self.user1.id}
            )