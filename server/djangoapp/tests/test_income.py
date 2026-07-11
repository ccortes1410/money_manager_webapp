"""
Tests for the Income model and its API endpoints.
"""

import json
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

from djangoapp.models.models import Income

from .test_base import BaseTestCase


class IncomeModelTests(BaseTestCase):
    def test_create_income_usual(self):
        income = self.create_income()
        self.assertEqual(income.source, 'Salary')

    def test_str_representation(self):
        income = self.create_income()
        expected = (
            f"Income {income.id}: {income.amount} from {income.source} "
            f"on {income.date_received} by {income.user.username}"
        )
        self.assertEqual(str(income), expected)

    def test_clean_raises_value_error_when_period_end_before_start(self):
        income = Income(
            user=self.user1,
            amount=Decimal('1000'),
            source='Freelance',
            period_start=self.today,
            period_end=self.today - timezone.timedelta(days=1)
        )
        with self.assertRaises(ValueError):
            income.clean()

    def test_clean_allows_equal_start_and_end(self):
        income = Income(
            user=self.user1, amount=Decimal('100'), source='Freelance',
            date_received=self.today, period_start=self.today, period_end=self.today,
        )
        income.clean()

    def test_negative_amount_fails_validation(self):
        income = Income(
            user=self.user1, amount=Decimal('-1'), source='Freelance',
            date_received=self.today, period_start=self.today, period_end=self.today
        )
        with self.assertRaises(Exception):
            income.full_clean()



class IncomeAPITests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user1)

    def test_get_incomes_requires_auth(self):
        self.client.logout()
        response = self.client.get(reverse('djangoapp:get_incomes'))
        self.assertEqual(response.status_code, 401)

    def test_get_incomes_returns_data(self):
        self.create_income()
        response = self.client.get(reverse('djangoapp:get_incomes'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['incomes']), 1)

    def test_get_income_endpoint_always_raises_bug(self):
        income = self.create_income()
        with self.assertRaises(AttributeError):
            self.client.get(reverse('djangoapp:get_income', kwargs={'income_id': income.id}))

    def test_income_create_endpoint_success(self):
        payload = {
            'amount': 2000,
            'source': 'Freelance',
            'date_received': self.today.isoformat(),
            'period_start': self.today.isoformat(),
            'period_end': (self.today + timezone.timedelta(days=14)).isoformat()
        }
        response = self.client.post(
            reverse('djangoapp:income_create'), data=json.dumps(payload), content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Income.objects.filter(user=self.user1, source='Freelance').exists())

    def test_income_create_endpoint_rejects_invalid_period(self):
        payload = {
            'amount': 2000,
            'source': 'Freelance',
            'date_received': self.today.isoformat(),
            'period_start': self.today.isoformat(),
            'period_end': (self.today - timezone.timedelta(days=1)).isoformat()
        }
        response = self.client.post(
            reverse('djangoapp:income_create'), data=json.dumps(payload), content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_income_create_endpoint_missing_field(self):
        response = self.client.post(
            reverse('djangoapp:income_create'), data=json.dumps({'amount': 100}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_income_update_endpoint_always_raises_bug(self):
        income = self.create_income()
        with self.asseretRaises(AttributeError):
            self.client.patch(
                reverse('djangoapp:income_udpdate', kwargs={'income_id': income.id}),
                data=json.dumps({'amount': 3000}), content_type='application/json'
            )
    
    def test_income_delete_endpoint(self):
        income = self.create_income()
        response = self.client.delete(
            reverse('djangoapp:income_delete'), data=json.dumps({'income_ids': [income.id]}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Income.objects.filter(id=income.id).exists())

    def test_income_delete_endpoint_no_ids_provided(self):
        response = self.client.delete(
            reverse('djangoapp:income_delete'), data=json.dumps({}), content_type='application/json'
        )
        self.assertIn('error', response.json())