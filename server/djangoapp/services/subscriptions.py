from ..models import Budget, Transaction, Subscription
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from decimal import Decimal
from .date_filter import filter_queryset_by_period
from .spending_calculations import get_subscription_amount_for_period, compute_subscription_total

def compute_subscription_summary(user):
    """Compute subscription summary for a user."""
    today = date.today()

    # Current month boundaries
    month_start = date(today.year, today.month, 1)
    if today.month == 12:
        month_end = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(today.year, today.month + 1, 1) - timedelta(days=1)
    
    active_subs = Subscription.objects.filter(user=user, is_active=True)
    inactive_subs = Subscription.objects.filter(user=user, is_active=False)

    # Calculate monthly cost of active subscriptions
    monthly_cost = Decimal('0')
    for sub in active_subs:
        if sub.billing_cycle == 'daily':
            monthly_cost += sub.amount * 30
        elif sub.billing_cycle == 'weekly':
            monthly_cost += sub.amount * Decimal('4')
        elif sub.billing_cycle == 'monbthly':
            monthly_cost += sub.amount
        elif sub.billing_cycle == 'yearly':
            monthly_cost += sub.amount / 12

    # This month's actual subscription spending
    this_month_total = compute_subscription_total(user, month_start, month_end)

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
                }
                for sub in inactive_subs
            ]
        },
        "this_month_total": float(this_month_total),
        "total_subscriptions": active_subs.count() + inactive_subs.count()
    }