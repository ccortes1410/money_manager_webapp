import json
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

from django.models.models import Budget

from .test_base import BaseTestCase


class BudgetModelTests(BaseTestCase):
    def test_create_budget_usual(self):
        budget = self.create_budget()
        self.assertTrue(budget.is_active)
        self.assertTrue(budget.is_recurring)
        self.assertFalse(budget.is_shared)

    def test_str_representation(self):
        budget = self.create_budget()
        self.assertEqual(str(budget), f"Category: {budget.category} by {budget.user.username}")

    def test_unique_category_per_user_enforced(self):
        self.create_budget()
        with self.assertRaises(Exception):
            from django.db import transaction
            with transaction.atomic():
                Budget.objects.create(
                    user=self.user1, category='Entertainment', amount=Decimal('500'),
                    period_start=self.today,
                    period_end=self.today + timezone.timedelta(days=10)
                )

    def test_same_category_different_users_allowed(self):
        self.create_budget()
        budget2 = Budget.objects.create(
            user=self.user2, category='Entertainment', amount=Decimal('500'),
            period_start=self.today,
            period_end=self.today + timezone.timedelta(days=10)
        )
        self.assertEqual(budget2.category, 'Entertainment')

    def test_negative_amount_fails_validation(self):
        budget = Budget(
            user=self.user1, category='Travel', amount=Decimal('-100'),
            period_start=self.today, period_end=self.today + timezone.timedelta(days=10)
        )
        with self.assertRaises(Exception):
            budget.full_clean()  # This will raise a ValidationError for negative amount

    def test_invalid_recurrence_choice_fails_validation(self):
        budget = Budget(
            user=self.user1, category='Travel', amount=Decimal('100'),
            period_start=self.today, period_end=self.today + timezone.timedelta(days=30),
            recurrence='biweekly'  # Invalid choice
        )
        with self.assertRaises(Exception):
            budget.full_clean()  # This will raise a ValidationError for invalid recurrence choice
    
    def test_recurrence_can_be_null(self):
        budget = Budget.objects.create(
            user=self.user1, category='Travel', amount=Decimal('100'),
            period_start=self.today, period_end=self.today + timezone.timedelta(days=30),
            recurrence=None  # Valid case
        )
        self.assertIsNone(budget.recurrence)


class BudgetAPITests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user1)

    def test_get_budgets_requires_auth(self):
        self.client.logout()
        response = self.client.get(reverse('djangoapp:budget_list'))
        self.assertEqual(response.status_code, 401)

    def test_create_budget_returns_active_budgets(self):
        self.create_budget()
        response = self.client.get(reverse('djangoapp:budget_list'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['budgets']), 1)

    def test_get_budget_detail_success(self):
        budget = self.create_budget()
        response = self.client.get(reverse('djangoapp:budget_detail', kwargs={'budget_id': budget.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['budget']['category'], 'Entertainment')

    def test_get_budget_detail_not_found(self):
        response = self.client.get(reverse('djangoapp:budget_detail', kwargs={'budget_id': 9999}))
        self.assertEqual(response.status_code, 404)

    def test_budget_create_endpoint(self):
        payload = {
            'category': 'Food',
            'amount': 300,
            'period_start': self.today.isoformat(),
            'period_end': (self.today + timezone.timedelta(days=30)).isoformat(),
        }
        response = self.client.post(
            reverse('djangoapp:budget_create'), data=json.dumps(payload), content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Budget.objects.filter(user=self.user1, category='Food').exists())

    def test_budget_create_endpoint_missing_field(self):
        payload = {'category': 'Food'}
        response = self.client.post(
            reverse('djangoapp:budget_create'), data=json.dumps(payload), content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_update_budget_endpoint_success(self):
        budget = self.create_budget()
        response = self.client.patch(
            reverse('djangoapp:budget_update', kwargs={'budget_id': budget.id}),
            data=json.dumps({'amount': 1500}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        budget.refresh_from_db()
        self.assertEqual(budget.amount, Decimal('1500'))

    def test_update_budget_endpoint_not_found_raises_bug(self):
        with self.assertRaises(NameError):
            self.client.patch(
                reverse('djangoapp:budget_update', kwargs={'budget_id: 9999'}),
                data=json.dumps({'amount': 1500}), content_type='application/json'
            )
    
    def test_toggle_recurring_endpoint(self):
        budget = self.create_budget()
        response = self.client.patch(
            reverse('djangoapp:toggle_budget_recurring', kwargs={'budget_id':budget.id}),
            data=json.dumps({'is_recurring': False}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        budget.refresh_from_db()
        self.assertFalse(budget.is_recurring)

    def test_budget_delete_endpoint(self):
        budget = self.create_budget()
        response = self.client.delete(
            reverse('djangoapp:budget_delete', kwargs={'budget_id': budget.id}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Budget.objects.filter(id=budget.id).exists())

    def test_budget_delete_endpoint_not_found(self):
        response = self.client.delete(reverse('djangoapp:delete_budget', kwargs={'budget_id': 9999}))
        self.assertEqual(response.status_code, 404)
