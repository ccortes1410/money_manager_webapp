"""
Tests for the Transaction model and its API endpoints.
"""


import json
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

from .test_base import BaseTestCase

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

    def test_list_requires_auth(self):
        self.client.logout()
        response = self.client.get(reverse('djangoapp:transactions'))
        self.assertEqual(response.status_code, 401)  # Unauthorized

    def test_list_returns_only_own_transactions(self):
        self.create_transaction()  # Transaction for user1
        Transaction.objects.create(
            user=self.user2, amount=Decimal('200'), description='Other user',
            category='Food', date=self.today
        )
        response = self.client.get(reverse('djangoapp:transactions'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['transactions']), 1)

    def test_list_filters_by_category(self):
        Transaction.objects.create(
            user=self.user1, amount=Decimal('100'),
            description='A', category='Food', date=self.today
        )
        Transaction.objects.create(
            user=self.user1, amount=Decimal('500'),
            description='B', category='Transport', date=self.today
        )
        response = self.client.get(reverse('djangoapp:transactions'), {'category': 'Food'})
        data = response.json()
        self.assertEqual(len(data['transactions']), 1)
        self.assertEqual(data['transactions'][0]['category'], 'Food')
        
    def test_post_via_transactions_enpoint_creates_transaction(self):
        payload = {
            'amount': 1500,
            'date': self.today.isoformat(),
            'description': 'Snacks',
            'category': 'Food'
        }
        response = self.client.post(
            reverse('djangoapp:transactions'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Transaction.objects.filter(user=self.user1).count(), 1)

    def test_delete_via_transactions_endpoint(self):
        tx1 = self.create_transaction()
        tx2 = Transaction.objects.create(
            user=self.user1, amount=Decimal('200'),
            description='Second', category='Food', date=self.today
        )
        response = self.client.delete(
            reverse('djangoapp:transactions'),
            data=json.dumps({'ids': [tx1.id]}),
                content_type='application/json'
            )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Transaction.objects.filter(id=tx1.id).exists())
        self.assertTrue(Transaction.objects.filter(id=tx2.id).exists())

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
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Transaction.objects.filter(user=self.user1, description='Lunch').exists())

    def tset_transaction_create_endpoint_missing_field(self):
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
        tx = self.create_transaction()
        response = self.client.patch(
            reverse('djangoapp:transaction_update', kwargs={'transaction_id': tx.id}),
            data=json.dumps({'amount': 2000}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        tx.refresh_from_db()
        self.assertEqual(tx.amount, Decimal('2000'))

    def test_transaction_delete_endopoint(self):
        tx = self.create_transaction()
        response = self.client.delete(
            reverse('djangoapp:transaction_delete'), 
            data=json.dumps({'ids': [tx.id]}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Transaction.objects.filter(id=tx.id).exists())