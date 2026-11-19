"""
Tests for the Subscription model and its API endpoints.
"""

import json
from decimal import Decimal
from datetime import timezone, timedelta

from django.urls import reverse

from djangoapp.models.models import Subscription
from djangoapp.services.subscription_service import generate_subscription_payments

from .test_base import BaseTestCase
from .test_api_backend import TestApiBackend
from unittest.mock import patch


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

    def _seed_subscription(self, **overrides):
        row = {
            "user_id": self.user1.id,
            "name": "Netflix",
            "amount": "9990.00",
            "category": "Entertainment",
            "billing_cycle": "monthly",
            "billing_day": self.today.day,
            "start_date": self.today.isoformat(),
            "end_date": (self.today + timedelta(days=30)).isoformat(),
            "status": "active",
            "description": "Netflix account",
            "created_at": self.today.isoformat(),
            "updated_at": self.today.isoformat()
        }
        row.update(overrides)
        return self.test_api.seed("subscriptions", row)

    def test_list_requires_auth(self):
        self.client.logout()
        response = self.client.get(reverse('djangoapp:subscriptions'))
        self.assertEqual(response.status_code, 401)


    def test_list_returns_data_when_subscription_exists(self):
        self._seed_subscription()
        response = self.client.get(reverse('djangoapp:subscriptions'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['subscriptions']), 1)
        self.assertEqual(data['subscriptions'][0]['name'], 'Netflix')
        self.assertEqual(data['subscriptions'][0]['created_at'], self.today.isoformat())

    def test_list_returns_all_subscriptions(self):
        self._seed_subscription(name="Netflix")
        self._seed_subscription(name="Music", status="paused")
        self._seed_subscription(name="Gym", status="cancelled")

        response = self.client.get(reverse('djangoapp:subscriptions'))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(
            {subscription['name'] for subscription in data['subscriptions']},
            {"Netflix", "Music", "Gym"},
        )

    def test_create_endpoint(self):
        payload = {
            'name': 'Hulu',
            'amount': 899,
            'category': 'Entertainment',
            'billing_cycle': 'monthly',
            'billing_day': self.today.day,
            'start_date': self.today.isoformat(),
        }
        response = self.client.post(
            reverse('djangoapp:subscriptions_create'),
            data=json.dumps(payload), content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        # Check that the subscription was added to the mock API
        subscriptions = self.test_api.resources.get("subscriptions", [])
        self.assertEqual(len(subscriptions), 1)
        self.assertEqual(subscriptions[0]['name'], 'Hulu')
        self.assertEqual(float(subscriptions[0]['amount']), 899.0)
        payments = self.test_api.resources.get("subscription-payments", [])
        self.assertEqual(len(payments), 1)
        self.assertEqual(payments[0]['user_id'], self.user1.id)
        self.assertEqual(payments[0]['subscription_id'], subscriptions[0]['id'])
        self.assertEqual(payments[0]['due_date'], self.today.isoformat())

    def test_monthly_payments_align_to_billing_day_and_clean_off_schedule(self):
        from datetime import date
        sub = self._seed_subscription(
            name="Netflix",
            billing_cycle="monthly",
            billing_day=15,
            start_date="2026-08-16",
            end_date=None,
        )
        # Seed off-schedule October payments (1st and 30th)
        self.test_api.seed("subscription-payments", {
            "user_id": self.user1.id,
            "subscription_id": sub["id"],
            "due_date": "2026-10-01",
            "amount": "9990.00",
            "is_paid": True,
            "paid_date": "2026-10-01",
        })
        self.test_api.seed("subscription-payments", {
            "user_id": self.user1.id,
            "subscription_id": sub["id"],
            "due_date": "2026-10-30",
            "amount": "9990.00",
            "is_paid": False,
            "paid_date": None,
        })

        generate_subscription_payments(self.user1.id, date(2026, 11, 14))
        payments = [
            p for p in self.test_api.resources["subscription-payments"]
            if p["subscription_id"] == sub["id"]
        ]
        due_dates = sorted(p["due_date"] for p in payments)
        self.assertEqual(due_dates, ["2026-09-15", "2026-10-15"])

    def test_api_payment_generation_catches_up_and_is_idempotent(self):
        start_date = self.today - timedelta(days=40)
        self._seed_subscription(
            start_date=start_date.isoformat(),
            end_date=None,
        )

        created_count = generate_subscription_payments(self.user1.id, self.today)
        repeated_count = generate_subscription_payments(self.user1.id, self.today)

        payments = self.test_api.resources["subscription-payments"]
        self.assertGreater(created_count, 1)
        self.assertEqual(repeated_count, 0)
        self.assertEqual(len(payments), created_count)

    def test_manual_unpaid_payment_is_preserved_across_reloads(self):
        sub = self._seed_subscription(
            start_date=self.today.isoformat(),
            end_date=None,
            billing_day=self.today.day,
        )
        generate_subscription_payments(self.user1.id, self.today)
        payments = [
            p for p in self.test_api.resources["subscription-payments"]
            if p["subscription_id"] == sub["id"]
        ]
        self.assertEqual(len(payments), 1)
        self.assertTrue(payments[0]["is_paid"])

        # Mark payment as unpaid via the toggle endpoint
        toggle_resp = self.client.patch(
            reverse('djangoapp:payment_toggle', kwargs={'payment_id': payments[0]["id"]})
        )
        self.assertEqual(toggle_resp.status_code, 200)
        self.assertFalse(toggle_resp.json()["payment"]["is_paid"])

        # Reload subscriptions (which triggers generate_subscription_payments again)
        list_resp = self.client.get(reverse('djangoapp:subscriptions'))
        self.assertEqual(list_resp.status_code, 200)

        reloaded_payments = [
            p for p in self.test_api.resources["subscription-payments"]
            if p["subscription_id"] == sub["id"]
        ]
        self.assertEqual(len(reloaded_payments), 1)
        self.assertFalse(reloaded_payments[0]["is_paid"])
        self.assertIsNone(reloaded_payments[0]["paid_date"])

    def test_detail_endpoint_success_with_end_date_set(self):
        sub = self._seed_subscription()
        response = self.client.get(
            reverse('djangoapp:subscription_detail', kwargs={'subscription_id': sub['id']})
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['subscription']['name'], sub['name'])
        

    def test_detail_endpoint_without_end_date_raises_bug(self):
        sub = self._seed_subscription(
            user=self.user1, name='NoEndDate', amount=Decimal('50'),
            category='A', start_date=self.today, end_date=None
        )
      
        with self.assertRaises(AttributeError):
            self.client.get(
                reverse('djangoapp:subscription_detail', kwargs={'subscription_id': sub.id})
            )

    def test_update_endpoint(self):
        sub = self._seed_subscription(name="Old Name")
        response = self.client.patch(
            reverse('djangoapp:subscription_update', kwargs={'subscription_id': sub['id']}),
            data=json.dumps({'name': 'Renamed'}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        # Check that the subscription was updated in the mock API
        updated_sub = next((s for s in self.test_api.resources["subscriptions"] if s["id"] == sub['id']), None)
        self.assertIsNotNone(updated_sub)
        self.assertEqual(updated_sub['name'], 'Renamed')

    def test_delete_endpoint(self):
        sub = self._seed_subscription()
        response = self.client.delete(
            reverse('djangoapp:subscription_delete', kwargs={'subscription_id': sub['id']})
        )
        self.assertEqual(response.status_code, 200)
        # Check that the subscription was deleted from the mock API
        subscriptions = self.test_api.resources.get("subscriptions", [])
        self.assertEqual(len(subscriptions), 0)

    def test_update_status_endpoint_sets_end_date_on_cancel(self):
        sub = self._seed_subscription()
        response = self.client.patch(
            reverse('djangoapp:subscription_status', kwargs={'subscription_id': sub['id']}),
            data=json.dumps({'status': 'cancelled'}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        # Check that the subscription was updated in the mock API
        updated_sub = next((s for s in self.test_api.resources["subscriptions"] if s["id"] == sub['id']), None)
        self.assertIsNotNone(updated_sub)
        self.assertEqual(updated_sub['status'], 'cancelled')
        self.assertIsNotNone(updated_sub['end_date'])

    def test_update_status_endpoint_rejects_invalid_status(self):
        sub = self._seed_subscription()
        response = self.client.patch(
            reverse('djangoapp:subscription_status', kwargs={'subscription_id': sub['id']}),
            data=json.dumps({'status': 'not_a_real_status'}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)