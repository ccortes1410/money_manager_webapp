"""
Tests for the Transaction model and its API endpoints.
"""


import json
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

from .test_base import BaseTestCase
from .test_api_backend import TestApiBackend
from unittest.mock import patch

from djangoapp.models.models import Transaction


class TransactionModelTests(BaseTestCase):
    def test_create_transaction_usual(self):
        tx = self.create_transaction()
        self.assertEqual(tx.amount, Decimal('1000'))
        self.assertEqual(tx.category, 'General')
        self.assertIsNotNone(tx.id)

    def test_str_representation(self):
        tx = self.create_transaction()
        expected_str = f"Transaction {tx.id}: {tx.amount} on {tx.date} by {tx.user.username}"
        self.assertEqual(str(tx), expected_str)

    def test_category_can_be_null(self):
        tx = Transaction.objects.create(
            user=self.user1, amount=Decimal('100'),
            description='No category', category=None, date=self.today
        )
        self.assertIsNone(tx.category)

    def test_negative_amount_fails_validation(self):
        tx = Transaction(
            user=self.user1, amount=Decimal('-100'),
            description='Negative', category='Food', date=self.today 
        )
        with self.assertRaises(Exception):
            tx.full_clean()  # This should raise a ValidationError

    def test_zero_amount_is_valid(self):
        tx = Transaction(
            user=self.user1, amount=Decimal('0'),
            description='Free item', category='Misc', date=self.today
        )
        tx.full_clean()  # Should not raise an exception

    def test_missing_description_fails_validation(self):
        tx = Transaction(
            user=self.user1, amount=Decimal('100'),
            description='', category='Misc', date=self.today
        )
        with self.assertRaises(Exception):
            tx.full_clean()  # This should raise a ValidationError


class TransactionAPITests(BaseTestCase):
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

    def _seed_transaction(self, **overrides):
        row = {
            "user_id": self.user1.id,
            "amount": "1000.00",
            "description": "Test Transaction",
            "category": "General",
            "date": self.today.isoformat(),
        }
        row.update(overrides)
        return self.test_api.seed("transactions", row)
        

    def test_list_requires_auth(self):
        self.client.logout()
        response = self.client.get(reverse('djangoapp:transactions'))
        self.assertEqual(response.status_code, 401)  # Unauthorized

    def test_list_returns_only_own_transactions(self):
        self._seed_transaction()  # Transaction for user1
        self.test_api.seed("transactions", {
            "user_id": self.user2.id,
            "amount": "200.00",
            "description": "Other user",
            "category": "Food",
            "date": self.today.isoformat(),
        })
        response = self.client.get(reverse('djangoapp:transactions'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['transactions']), 1)

    def test_list_filters_by_category(self):
        self._seed_transaction(description='A', category='Food')
        self.test_api.seed("transactions", {
            "user_id": self.user1.id,
            "amount": "500.00",
            "description": "B",
            "category": "Transport",
            "date": self.today.isoformat(),
        })
        response = self.client.get(reverse('djangoapp:transactions'), {'category': 'Food'})
        data = response.json()
        self.assertEqual(len(data['transactions']), 1)
        self.assertEqual(data['transactions'][0]['category'], 'Food')
        
    def test_post_via_transactions_endpoint_creates_transaction(self):
        payload = {
            'amount': 1500,
            'date': self.today.isoformat(),
            'description': 'Snacks',
            'category': 'Food'
        }
        response = self.client.post(
            reverse('djangoapp:transaction_create'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        # Check that the transaction was added to the mock API
        transactions = self.test_api.resources.get("transactions", [])
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0]['description'], 'Snacks')
        self.assertEqual(float(transactions[0]['amount']), 1500.0)

    def test_delete_via_transactions_endpoint(self):
        tx1 = self._seed_transaction()
        tx2 = self.test_api.seed("transactions", {
            "user_id": self.user1.id,
            "amount": "200.00",
            "description": "Second",
            "category": "Food",
            "date": self.today.isoformat(),
        })
        response = self.client.delete(
            reverse('djangoapp:transaction_delete'),
            data=json.dumps({'ids': [tx1['id']]}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        # Check that tx1 was deleted from the mock API but tx2 still exists
        transactions = self.test_api.resources.get("transactions", [])
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0]['id'], tx2['id'])

    def test_transaction_create_endpoint_success(self):
        payload = {
            'amount': 1000,
            'description': 'Lunch',
            'category': 'Food',
            'date': self.today.isoformat()
        }
        response = self.client.post(
            reverse('djangoapp:transaction_create'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

        transaction = self.test_api.resources.get("transactions", [])
        self.assertEqual(len(transaction), 1)

    def test_transaction_create_endpoint_missing_field(self):
        payload = {
            'amount': 1000,
            'description': 'Lunch',
        }
        response = self.client.post(
            reverse('djangoapp:transaction_create'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_transaction_update_endpoint_updates_amount(self):
        tx = self._seed_transaction()
        response = self.client.patch(
            reverse('djangoapp:transaction_update', kwargs={'transaction_id': tx["id"]}),
            data=json.dumps({'amount': 2000}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        updated = self.test_api.resources.get("transactions", [])
        self.assertEqual(Decimal(updated[0]['amount']), Decimal('2000'))

    def test_transaction_delete_endpoint(self):
        tx = self._seed_transaction()
        response = self.client.delete(
            reverse('djangoapp:transaction_delete'),
            data=json.dumps({'ids': [tx['id']]}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        # Check that the transaction was deleted from the mock API
        transactions = self.test_api.resources.get("transactions", [])
        self.assertEqual(len(transactions), 0)