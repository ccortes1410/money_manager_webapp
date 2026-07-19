"""
Tests for the Subscription model and its API endpoints.
"""

import json
from decimal import Decimal

from django.urls import reverse

from djangoapp.models.models import Subscription

from .test_base import BaseTestCase


class SubscriptionModelTests(BaseTestCase):
    def test_create_subscription_usual(self):
        sub = self.create_subscription()
        self.assertEqual(sub.status, 'active')
        self.assertEqual(sub.billing_cycle, 'monthly')

    def test_str_representation(self):
        sub = self.create_subscription()
        self.assertEqual(str(sub), f"{sub.name} - ${sub.amount}/{sub.billing_cycle}")

    def test_defaults_billing_cycle_and_day(self):
        sub = Subscription.objects.create(
            user=self.user1, name='Spotify', amount=Decimal('999'),
            category='Entertainment', start_date=self.today
        )
        self.assertEqual(sub.billing_cycle, 'monthly')
        self.assertEqual(sub.billing_day, 1)
        self.assertEqual(sub.status, 'active')

    def test_negative_amount_fails_validation(self):
        sub = Subscription(
            user=self.user1, name='Bad', amount=Decimal('-50'),
            category='Test', start_date=self.today
        )
        with self.assertRaises(Exception):
            sub.full_clean()
        
    def test_ordering_is_alphabetical_by_name(self):
        Subscription.objects.create(
            user=self.user1, name='Zeta', amount=Decimal('50'),
            category='A', start_date=self.today
        )
        Subscription.objects.create(
            user=self.user1, name='Alpha', amount=Decimal('50'),
            category='A', start_date=self.today
        )
        names = list(Subscription.objects.filter(user=self.user1).values_list('name', flat=True))
        self.assertEqual(names, sorted(names))


class SubscriptionAPITests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user1)

    def test_list_requires_auth(self):
        self.client.logout()
        response = self.client.get(reverse('djangoapp:subscriptions'))
        self.assertEqual(response.status_code, 401)

    def test_list_with_no_subscriptions_returns_500_bug(self):
        response = self.client.get(reverse('djangoapp:subscriptions'))
        self.assertEqual(response.status_code, 500)

    def test_list_returns_data_when_subscription_exists(self):
        self.create_subscription()
        response = self.client.get(reverse('djangoapp:subscriptions'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['subscriptions']), 1)

    def test_create_endpoint(self):
        payload = {
            'name': 'Hulu',
            'amount': 899,
            'category': 'Entertainment',
            'billing_cycle': 'monthly',
            'billing_day': 15,
            'start_date': self.today.isoformat(),
        }
        response = self.client.post(
            reverse('djangoapp:subscriptions_create'),
            data=json.dumps(payload), content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Subscription.objects.filter(user=self.user1, name='Hulu').exists())

    def test_detail_endpoint_success_with_end_date_set(self):
        sub = self.create_subscription()
        response = self.client.get(
            reverse('djangoapp:subscription_detail', kwargs={'subscription_id': sub.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['subscription']['name'], sub.name)

    def test_detail_endpoint_without_end_date_raises_bug(self):
        sub = Subscription.objects.create(
            user=self.user1, name='NoEndDate', amount=Decimal('50'),
            category='A', start_date=self.today, end_date=None
        )
        with self.assertRaises(AttributeError):
            self.client.get(
                reverse('djangoapp:subscription_detail', kwargs={'subscription_id': sub.id})
            )

    def test_update_endpoint(self):
        sub = self.create_subscription()
        response = self.client.patch(
            reverse('djangoapp:subscription_update', kwargs={'subscription_id': sub.id}),
            data=json.dumps({'name': 'Renamed'}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        sub.refresh_from_db()
        self.assertEqual(sub.name, 'Renamed')

    def test_delete_endpoint(self):
        sub = self.create_subscription()
        response = self.client.delete(
            reverse('djangoapp:subscription_delete', kwargs={'subscription_id': sub.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Subscription.objects.filter(id=sub.id).exists())

    def test_update_status_endpoint_sets_end_date_on_cancel(self):
        sub = self.create_subscription()
        response = self.client.patch(
            reverse('djangoapp:subscription_status', kwargs={'subscription_id': sub.id}),
            data=json.dumps({'status': 'cancelled'}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        sub.refresh_from_db()
        self.assertEqual(sub.status, 'cancelled')
        self.assertIsNotNone(sub.end_date)

    def test_update_status_endpoint_rejects_invalid_status(self):
        sub = self.create_subscription()
        response = self.client.patch(
            reverse('djangoapp:subscription_status', kwargs={'subscription_id': sub.id}),
            data=json.dumps({'status': 'not_a_real_status'}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)