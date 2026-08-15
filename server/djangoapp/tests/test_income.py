"""
Tests for the Income model and its API endpoints.
"""

import json
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

from djangoapp.models.models import Income

from .test_base import BaseTestCase
from .test_api_backend import TestApiBackend
from unittest.mock import patch


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

    def test_get_incomes_requires_auth(self):
        self.client.logout()
        response = self.client.get(reverse('djangoapp:get_incomes'))
        self.assertEqual(response.status_code, 401)

    def _seed_income(self, **overrides):
        row = {
            "user_id": self.user1.id,
            "amount": "5000.00",
            "source": "Salary",
            "date_received": self.today.isoformat(),
            "period_start": self.today.replace(day=1).isoformat(),
            "period_end": (self.today.replace(day=28) + timezone.timedelta(days=3)).isoformat(),
        }
        row.update(overrides)
        return self.test_api.seed("incomes", row)

    def test_get_incomes_returns_data(self):
        self._seed_income()
        response = self.client.get(reverse('djangoapp:get_incomes'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['incomes']), 1)
        self.assertEqual(data['incomes'][0]['source'], 'Salary')
        self.assertEqual(float(data['incomes'][0]['amount']), 5000.00)

    def test_get_income_endpoint_success(self):
        income = self._seed_income()
        response = self.client.get(reverse('djangoapp:get_income', kwargs={'income_id': income['id']}))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['income']['id'], income['id'])
        self.assertEqual(data['income']['source'], income['source'])
        self.assertEqual(float(data['income']['amount']), float(income['amount']))

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
        # Check that the income was added to the mock API
        incomes = self.test_api.resources.get("incomes", [])
        self.assertEqual(len(incomes), 1)
        self.assertEqual(incomes[0]['source'], 'Freelance')
        self.assertEqual(float(incomes[0]['amount']), 2000.0)

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

    def test_income_update_endpoint_updates_amount(self):
        income = self._seed_income(amount="1500.00")
        response = self.client.patch(
            reverse('djangoapp:income_update', kwargs={'income_id': income['id']}),
            data=json.dumps({'amount': 3000}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        # Check that the income was updated in the mock API
        updated_income = next((i for i in self.test_api.resources["incomes"] if i["id"] == income['id']), None)
        self.assertIsNotNone(updated_income)
        self.assertEqual(float(updated_income['amount']), 3000.0)
    
    def test_income_delete_endpoint(self):
        income = self._seed_income()
        response = self.client.delete(
            reverse('djangoapp:income_delete'), data=json.dumps({'income_ids': [income["id"]]}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Income.objects.filter(id=income["id"]).exists())

    def test_income_delete_endpoint_no_ids_provided(self):
        response = self.client.delete(
            reverse('djangoapp:income_delete'), data=json.dumps({}), content_type='application/json'
        )
        self.assertIn('error', response.json())