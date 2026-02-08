from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth, Coalesce
from decimal import Decimal
from ..models import Income, Transaction, Subscription, Budget

def get_subscription_amount_for_period(subscription, period_start, period_end):
    """
    Calculate how much a subscription costs within a given period.
    Takes into account billing cycle and weather the subscription is active.
    """

    if not subscription.status != 'active':
        return Decimal('0')
    
    # If subscription started after period ends or hasn't started yet
    if subscription.start_date > period_end:
        return Decimal('0')
    
    # If subscription has an end date and ended before period starts
    if subscription.end_date and subscription.end_date < period_start:
        return Decimal('0')
    
    # Dtermine the effective period for thos subscription
    effective_start = max(subscription.start_date, period_start)
    effective_end = period_end
    if subscription.end_date:
        effective_end = min(subscription.end_date, period_end)
    
    # Calculate number of billing cycles in the period
    amount = subscription.amount
    billing_cycle = subscription.billing_cycle

    if billing_cycle == 'daily':
        days = (effective_end - effective_start).days + 1
        return amount * days
    
    elif billing_cycle == 'weekly':
        days = (effective_end - effective_start).days + 1
        weeks = days / 7
        return amount * Decimal(str(weeks))
    
    elif billing_cycle == 'monthly':
        # Count months between effective_start and effective_end
        months = 0
        current = effective_start.replace(day=1)
        while current <= effective_end:
            # Check if billing would occur this month
            billing_day = min(subscription.billing_day or 1, 28) # Safe day
            try:
                billing_date = current.replace(day=billing_day)
            except ValueError:
                # Handle months with fewer days
                billing_day = current.replace(day=28)

            if effective_start <= billing_date <= effective_end:
                months += 1

            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

    elif billing_cycle == 'yearly':
        # Check if yearly billing occurs within period
        years = 0
        current_year = effective_start.year
        while current_year <= effective_end.year:
            try:
                billing_date = date(
                    current_year,
                    subscription.start_date.month,
                    subscription.start_date.day
                )
            except ValueError:
                billing_date = date(current_year, subscription.start_date.month, 28)
            
            if effective_start <= billing_date <= effective_end:
                years += 1
            current_year += 1
        
        return amount * max(1, years) # At least 1 if period overlaps
    
    return amount

def compute_transaction_total(user, period_start=None, period_end=None, category=None):
    """Calculate total from transactions."""
    queryset = Transaction.objects.filter(user=user)

    if period_start:
        queryset = queryset.filter(date__gte=period_start)
    if period_end:
        queryset = queryset.filter(date__lte=period_end)
    if category:
        queryset = queryset.filter(category__iexact=category)
    
    result = queryset.aggregate(total=Sum("amount"))
    return result["total"] or Decimal('0')

def compute_subscription_total(user, period_start=None, period_end=None, category=None):
    """Calculate total from active subscriptions for a period."""
    queryset = Subscription.objects.filter(user=user, status='active')

    if category:
        queryset = queryset.filter(category__iexact=category)
    
    # If no perio specified, use current month
    if not period_start or not period_end:
        today = date.today()
        period_start = date(today.year, today.month, 1)
        if today.month == 12:
            period_end = date(today.year + 1, 1, 1) -timedelta(days=1)
        else:
            period_end = date(today.year, today.month + 1, 1) - timedelta(days=1)
    
    total = Decimal('0')
    for subscription in queryset:
        total += get_subscription_amount_for_period(subscription, period_start, period_end)
    
    return total

def compute_total_spent(user, period_start=None, period_end=None, category=None):
    """Calculate total spent (transactions + subscriptions) for a user."""
    transaction_total = compute_transaction_total(user, period_start, period_end, category)
    subscription_total = compute_subscription_total(user, period_start, period_end, category)

    return {
        "total": float(transaction_total + subscription_total),
        "transactions": float(transaction_total),
        "subscriptions": float(subscription_total),
    }

