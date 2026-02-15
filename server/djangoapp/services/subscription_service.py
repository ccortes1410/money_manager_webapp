from datetime import date, timedelta
from calendar import monthrange
from django.db.models import Sum
from django.utils import timezone
from django.db import IntegrityError
from .spending_calculations import compute_subscription_total
from ..models.models import Subscription, SubscriptionPayment


def generate_subscription_payments(user, up_to_date=None):
    """ 
    Generate SubcriptionPayment records for all active subscriptions
    up to the specified date (default: today).

    Call this daily via scheduled task, or on-demand.
    """
    if up_to_date is None:
        up_to_date = timezone.now().date()

    subscriptions = Subscription.objects.filter(
        user=user,
        status='active'
    )

    created_count = 0

    for subscription in subscriptions:
        payments = generate_payments_for_subscription(subscription, up_to_date)
        created_count += len(payments)

    return created_count

def generate_payments_for_subscription(subscription, up_to_date):
    """
    Generate all missing SubscriptionPayment records for a subscription
    from start_date to up_to_date.
    """
    created_payments = []

    # Get all billing dates from start to now
    billing_dates = get_billing_dates(
        start_date=subscription.start_date,
        end_date=up_to_date,
        billing_cycle=subscription.billing_cycle,
        billing_day=subscription.billing_day
    )

    for billing_date in billing_dates:
        # Skip if subscription was ended before this date
        if subscription.end_date and billing_date > subscription.end_date:
            continue

        try:
            payment, created = SubscriptionPayment.objects.get_or_create(
                subscription=subscription,
                date=billing_date,
                defaults={
                    'amount': subscription.amount,
                    'is_paid': True,
                    'paid_date': billing_date,
                }
            )

            if created:
                created_payments.append(payment)
        except IntegrityError:
            # Payment already exists
            pass

        return created_payments
    
def get_billing_dates(start_date, end_date, billing_cycle, billing_day=1):
    """
    Calculate all billing dates between start_date and end_date.
    """

    dates = []
    current = start_date

    while current <= end_date:
        dates.append(current)
        current = get_next_billing_date(current, billing_cycle, billing_day)

        # Safety: prevent infinite loop
        if len(dates) > 1000:
            break

    return dates

def get_next_billing_date(from_date, billing_cycle, billing_day=1):
    """Calculate the next billing date after from_date."""

    if billing_cycle == "daily":
        return from_date + timedelta(days=1)
    elif billing_cycle == "weekly":
        return from_date + timedelta(weeks=1)
    elif billing_cycle == "monthly":
        year, month = from_date.year, from_date.month

        # Move to next month
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1

        # Handle months with fewer days
        max_day = monthrange(year, month)[1]
        day = min(billing_day, max_day)

        return from_date.replace(year=year, month=month, day=day)
    elif billing_cycle == "yearly":
        return from_date.replace(year=from_date.year + 1)
    
    return from_date + timedelta(days=31)   # Default fallback

def get_subscriptions_for_period(user, period: str):
    """
    Get subscription payment totals for a period.
    Used by dashboard.
    """
    from .date_filter import filter_queryset_by_period

    payments = filter_queryset_by_period(
        SubscriptionPayment.objects.filter(subscription__user=user),
        period=period,
        date_field="date"
    )

    active_payments = payments.filter(subscription__status='active')
    inactive_payments = payments.filter(subscription__status__in=['paused', 'cancelled'])
    print("Subs for period:", active_payments)
    return {
        "active": {
            "count": active_payments.values('subscription').distinct().count(),
            "total": float(active_payments.aggregate(total=Sum('amount'))['total'] or 0),
            "payments": list(active_payments.values(
                'id', 'amount', 'date',
                'subscription__name', 'subscription__category'
            ))
        },
        "inactive": {
            "count": inactive_payments.values('subscription').distinct().count(),
            "total": float(inactive_payments.aggregate(total=Sum('amount'))['total'] or 0)
        },
        "total": float(payments.aggregate(total=Sum('amount'))['total'] or 0),
        "payment_count": payments.count()
    }

def compute_subscription_summary(user):
    """Compute subscription summary for a user."""
    today = date.today()

    # Current month boundaries
    month_start = date(today.year, today.month, 1)
    if today.month == 12:
        month_end = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(today.year, today.month + 1, 1) - timedelta(days=1)
    
    active_subs = Subscription.objects.filter(user=user, status='active')
    inactive_subs = Subscription.objects.filter(user=user).exclude(status='active')

    # Calculate monthly cost of active subscriptions
    monthly_cost = 0
    for sub in active_subs:
        payments = SubscriptionPayment.filter
        if sub.billing_cycle == 'daily':
            monthly_cost += payments * 30
        elif sub.billing_cycle == 'weekly':
            monthly_cost += payments * 4
        elif sub.billing_cycle == 'monbthly':
            monthly_cost += payments
        elif sub.billing_cycle == 'yearly':
            monthly_cost += payments / 12

    # This month's actual subscription spending
    this_month_total = compute_subscription_total(user, month_start, month_end)
    print("This month total (Subscriptions):", this_month_total)
    return {
        "active": {
            "count": active_subs.count(),
            "monthly_cost": float(monthly_cost),
            "items": [
                {
                    "id": sub.id,
                    "name": sub.name,
                    "amount": float(sub.amount),
                    "billing_cycle": sub.billing_cycle,
                    "category": sub.category,
                    "payments": sub.payments
                }
                for sub in active_subs
            ]
        },
        "inactive": {
            "count": inactive_subs.count(),
            "items": [
                {
                    "id": sub.id,
                    "name": sub.name,
                    "amount": float(sub.amount),
                    "billing_cycle": sub.billing_cycle,
                    "category": sub.category,
                    "payments": sub.payments
                }
                for sub in inactive_subs
            ]
        },
        "this_month_total": float(this_month_total),
        "total_subscriptions": active_subs.count() + inactive_subs.count()
    }

