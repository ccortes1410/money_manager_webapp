"""
Tests for recurrence functionality: Budget (recurring budgets that should
recreate themselves once their period expires) and Subscription (recurring
billing/payment generation).
 
Known bugs documented here:
 
  1. Budget recurrence is fundamentally broken. reset_expired_budgets()
     deactivates the expired Budget row (is_active=False) but leaves it in
     the table, then tries to Budget.objects.create() a *new* row for the
     next period with the same category + user. Since
     Budget.Meta.unique_together = ('category', 'user') doesn't take
     is_active into account, that create() always collides with the row
     that was just deactivated, raising IntegrityError. A recurring budget
     can never actually recur as currently written.
 
  2. generate_payments_for_subscription() has two stacked bugs:
     a) It calls
        SubscriptionPayment.objects.get_or_create(subscription=subscription,
        date=billing_date, ...), but SubscriptionPayment has no `date`
        field (only `paid_date`). This raises FieldError as soon as
        there's at least one billing date to process.
     b) Even setting that aside, `return created_payments` is indented
        *inside* the `for billing_date in billing_dates:` loop, so the
        function always returns after at most one billing date --
        subsequent billing dates in the range are silently never
        processed. GetBillingDatesTests below shows the date math itself
        is correct; it's purely the persistence function that stops
        short.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import FieldError
from django.db import IntegrityError, transaction

from djangoapp.models.models import Budget, Subscription
from djangoapp.services.budgets import calculate_next_period, reset_expired_budgets
from djangoapp.services.subscription_service import (
    generate_payments_for_subscription,
    generate_subscription_payments,
    get_billing_dates,
    get_next_billing_date
)

from .test_base import BaseTestCase


class CalculateNextPeriodTests(BaseTestCase):
    """calculate_next_period() is a pure function -- no DB writes."""

    def test_daily_recurrence(self):
        next_start, next_end = calculate_next_period(self.today, 'daily')
        self.assertEqual(next_start, self.today + timedelta(days=1))
        self.assertEqual(next_end, next_start)

    def test_weekly_recurrence_spans_seven_days(self):
        next_start, next_end = calculate_next_period(self.today, 'weekly')
        self.assertEqual(next_start, self.today + timedelta(days=1))
        self.assertEqual((next_end - next_start).days, 6)

    def test_monthly_recurrence_rolls_to_next_month(self):
        next_start, next_end = calculate_next_period(date(2026, 1, 31), 'monthly')
        self.assertEqual(next_start, date(2026, 2, 1))
        self.assertEqual(next_end, date(2026, 2, 28))

    def test_yearly_recurrence_rolls_to_next_year(self):
        next_start, next_end = calculate_next_period(date(2025, 12, 31), 'yearly')
        self.assertEqual(next_start, date(2026, 1, 1))
        self.assertEqual(next_end, date(2026, 12, 31))

    def test_invalid_recurrence_defaults_to_monthly(self):
        next_start, next_end =calculate_next_period(date(2026, 1, 31), 'biweekly')
        self.assertEqual(next_start, date(2026, 2, 1))
        self.assertEqual(next_end, date(2026, 2, 28))


class ResetExpiredBudgetsTests(BaseTestCase):
    def _make_expired_budgets(self, category='Groceries', recurrence='monthly', is_recurring=True, days_expired=5):
        period_end = self.today - timedelta(days=days_expired)
        period_start = period_end - timedelta(days=29)
        return Budget.objects.create(
            user=self.user1, category=category, amount=Decimal('200'),
            period_start=period_start, period_end=period_end,
            recurrence=recurrence, is_active=True, is_recurring=is_recurring, is_shared=False,
        )

    def test_non_recurring_expired_budget_is_deactivated_without_recreation(self):
        budget = self._make_expired_budgets(is_recurring=False)
        created = reset_expired_budgets(self.user1)
        budget.refresh_from_db()
        self.assertFalse(budget.is_active)
        self.assertEqual(created, [])
        self.assertEqual(Budget.objects.filter(user=self.user1).count(), 1)

    def test_active_non_expired_budget_is_left_alone(self):
        budget = self.create_budget()
        reset_expired_budgets(self.user1)
        budget.refresh_from_db()
        self.assertTrue(budget.is_active)

    def test_recurring_expired_budget_raises_unique_together_bug(self):
        """
        This is the core recurrence feature this whole module exists for
        -- and it currentl cannot work at all. See bug #1 in the module
        docstring.
        """
        self._make_expired_budgets(is_recurring=True)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                reset_expired_budgets(self.user1)

    def test_reset_only_processes_the_given_users_budgets(self):
        self._make_expired_budgets(is_recurring=False)
        other_expired = Budget.objects.create(
            user=self.user2, category='Other', amount=Decimal('10'),
            period_start=self.today - timedelta(days=40),
            period_end=self.today - timedelta(days=10),
            recurrence='monthly', is_active=True, is_recurring=False,
        )
        reset_expired_budgets(self.user1)
        other_expired.refresh_from_db()
        self.assertTrue(other_expired.is_active)


class GetNextBillingDateTests(BaseTestCase):
    def test_daily(self):
        self.assertEqual(get_next_billing_date(self.today, 'daily'), self.today + timedelta(days=1))

    def test_weekly(self):
        self.assertEqual(get_next_billing_date(self.today, 'weekly'), self.today + timedelta(weeks=1))

    def test_monthly_rolls_over_year_boundary(self):
        result = get_next_billing_date(date(2025, 12, 15), 'monthly', billing_day=15)
        self.assertEqual(result, date(2026, 1, 15))

    def test_monthly_clamps_billing_day_to_shorter_month(self):
        result = get_next_billing_date(date(2026, 1, 31), 'monthly', billing_day=31)
        self.assertEqual(result, date(2026, 2, 28))

    def test_yearly(self):
        self.assertEqual(get_next_billing_date(date(2025, 6, 1), 'yearly'), date(2026, 6, 1))

    def test_unknown_cycle_falls_back_to_31_days(self):
        self.assertEqual(get_next_billing_date(self.today, 'quarterly'), self.today + timedelta(days=31))


class GetBillingDatesTests(BaseTestCase):
    """
    Confirms the underlying date-range logic is correct on its own --
    useful contet for the persistence bug documented below, since it
    shows the bug is in generate_payments_for_subscription(), not in how
    billing dates are calculated.
    """

    def test_daily_cycle_returns_one_date_per_day(self):
        start = self.today
        end = self.today + timedelta(days=4)
        dates = get_billing_dates(start, end, 'daily')
        self.assertEqual(len(dates), 5)
        self.assertEqual(dates[0], start)
        self.assertEqual(dates[-1], end)

    def test_monthly_cycle_returns_one_date_per_month(self):
        start = date(2026, 1, 15)
        end = date(2026, 4, 15)
        dates = get_billing_dates(start, end, 'monthly', billing_day=15)
        self.assertEqual(dates, [date(2026, 1, 15), date(2026, 2, 15), date(2026, 3, 15), date(2026, 4, 15)])

    def test_start_after_end_returns_empty(self):
        dates = get_billing_dates(self.today, self.today- timedelta(days=1), 'daily')
        self.assertEqual(dates, [])


class SubscriptionPaymentGenerationBugTests(BaseTestCase):
    """
    Both generate_payments_for_subscription() and its caller
    generate_subscription_payments() are currently unusable -- see bug #2
    in the module docstring. Once the 'date' -> 'paid_date' field name is
    fixed, re-run these; they should then instead start exposing the
    second bug (the misplaced 'return' inside the loop), at which point
    these tests should be replaced with ones asserting that ALL expected
    billing dates in the range produced a SubscriptionPayment, not just
    the first one.
    """

    def test_generate_payments_for_subscription_raises_field_error_bug(self):
        sub = self.create_subscription()
        with self.assertRaises(FieldError):
            generate_payments_for_subscription(sub, self.today)

    def test_generate_subscription_payment_raises_field_error_bug(self):
        self.create_subscription()
        with self.assertRaises(FieldError):
            generate_subscription_payments(self.user1, up_to_date=self.today)