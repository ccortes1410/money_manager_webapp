"""
Tests for the SubscriptionPayment model and payment_toggle_paid endpoint.
"""

import json
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

from djangoapp.models.models import Subscription, SubscriptionPayment

from .test_base import BaseTestCase


class SusbcriptionPaymentModelTests(BaseTestCase):
    def test_create_payment_usual(self):
        payment = self.create_subscription_payment()
        self.assertFalse(payment.is_paid)
        self.assertIsNone(payment.paid_date)
        self.assertEqual(payment.due_date, self.today)

    def test_str_representation(self):
        payment = self.create_subscription_payment()
        expected = f"{payment.subscription.name} - ${payment.amount} due {payment.due_date} (unpaid)"
        self.assertEqual(str(payment), expected)

    def test_str_representation_paid(self):
        payment = self.create_subscription_payment()
        payment.is_paid = True
        payment.paid_date = self.today
        payment.save()
        expected = f"{payment.subscription.name} - ${payment.amount} due {payment.due_date} (paid)"
        self.assertEqual(str(payment), expected)

    def test_unique_together_subscription_and_due_date(self):
        from django.db import IntegrityError, transaction
        sub = self.create_subscription()
        SubscriptionPayment.objects.create(
            subscription=sub, amount=sub.amount, due_date=self.today
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SubscriptionPayment.objects.create(
                    subscription=sub, amount=sub.amount, due_date=self.today
                )

    def test_same_due_date_different_subscription_allowed(self):
        sub1 = self.create_subscription()
        sub2 = Subscription.objects.create(
            user=self.user1, name='Other', amount=Decimal('500'),
            category='A', start_date=self.today
        )
        SubscriptionPayment.objects.create(subscription=sub1, amount=sub1.amount, due_date=self.today)
        payment2 = SubscriptionPayment.objects.create(subscription=sub2, amount=sub2.amount, due_date=self.today)
        self.assertIsNotNone(payment2.id)

    def test_ordering_by_due_date_descending(self):
        sub = self.create_subscription()
        older = SubscriptionPayment.objects.create(
            subscription=sub, amount=sub.amount,
            due_date=self.today - timezone.timedelta(days=10)
        )
        newer = SubscriptionPayment.objects.create(subscription=sub, amount=sub.amount, due_date=self.today)
        payments = list(SubscriptionPayment.objects.filter(subscription=sub))
        self.assertEqual(payments[0], newer)
        self.assertEqual(payments[1], older)

    def test_due_date_is_required(self):
        sub = self.create_subscription()
        payment = SubscriptionPayment(subscription=sub, amount=sub.amount)
        with self.assertRaises(Exception):
            payment.full_clean()

    def test_paid_date_defaults_to_null_regardless_of_due_date(self):
        """paid_date should never get auto-populated just because a
        payment was generated -- it's strictly a user action via the
        toggle endpoint.
        """
        payment = self.create_subscription_payment()
        self.assertIsNone(payment.paid_date)

class SubscriptionPaymentAPITests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user1)

    def test_toggle_requires_auth(self):
        self.client.logout()
        payment = self.create_subscription_payment()
        response = self.client.patch(reverse('djangoapp:payment_toggle', kwargs={'payment_id': payment.id}))
        self.assertEqual(response.status_code, 401)

    def test_toggle_flips_is_paid_and_sets_paid_date(self):
        payment = self.create_subscription_payment()
        self.assertFalse(payment.is_paid)
        response = self.client.patch(
            reverse('djangoapp:payment_toggle', kwargs={'payment_id': payment.id})
        )
        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        self.assertTrue(payment.is_paid)
        self.assertIsNotNone(payment.paid_date)

    def test_toggle_twice_clears_paid_date_but_keeps_due_date(self):
        payment = self.create_subscription_payment()
        self.client.patch(reverse('djangoapp:payment_toggle', kwargs={'payment_id': payment.id}))
        self.client.patch(reverse('djangoapp:payment_toggle', kwargs={'payment_id': payment.id}))
        payment.refresh_from_db()
        self.assertFalse(payment.is_paid)
        self.assertIsNone(payment.paid_date)
        self.assertEqual(payment.due_date, self.today)
        
    def test_toggle_not_found(self):
        response = self.client.patch(reverse('djangoapp:payment_toggle', kwargs={'payment_id': 9999}))
        self.assertEqual(response.status_code, 404)

    def test_toggle_only_affects_own_subscription(self):
        other_sub = Subscription.objects.create(
            user=self.user2, name='Other', amount=Decimal('500'), category='A', start_date=self.today
        )
        payment = SubscriptionPayment.objects.create(subscription=other_sub, amount=Decimal('500'), due_date=self.today)
        response = self.client.patch(reverse('djangoapp:payment_toggle', kwargs={'payment_id': payment.id}))
        self.assertEqual(response.status_code, 404)