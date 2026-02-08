from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from ..models import Income, Transaction
from .spending_calculations import compute_total_spent

def get_income_for_period(user, period_start=None, period_end=None):
    """Get income records for a specific period."""
    queryset = Income.objects.filter(user=user)

    if period_start:
        queryset = queryset.filter(period_end__gte=period_start)
    if period_end:
        queryset = queryset.filter(period_start__lte=period_end)

    return queryset.order_by('-date_received')

def compute_total_income(user, period_start=None, period_end=None):
    queryset = Income.objects.filter(user=user)

    if period_start:
        queryset = queryset.filter(period_end__gte=period_start)
    if period_end:
        queryset = queryset.filter(period_start__lte=period_end)

    result = queryset.aggregate(total=Sum("amount"))
    return float(result["total"] or 0)

def compute_income_summary(user):
    """Compute complete income summary for a user."""
    today = date.today()

    # Current month boundaries
    month_start = date(today.year, today.month, 1)
    if today.month == 12:
        month_end = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(today.year, today.month + 1, 1) - timedelta(days=1)

    # All time totals
    total_income = compute_total_income(user)
    spent_breakdown = compute_total_spent(user)
    total_spent = spent_breakdown["total"]

    # This month totals
    this_month_income = compute_total_income(user, month_start, month_end)
    this_month_spent_breakdown = compute_total_spent(user, month_start, month_end)
    this_month_spent = this_month_income - this_month_spent_breakdown["total"]

    # Remaining calculations
    remaining = total_income - total_spent
    this_month_remaining = this_month_income - this_month_spent

    # Percentages
    percent_remaining = (remaining / total_income * 100) if total_income > 0 else 0
    percent_remaining = max(0, min(100, percent_remaining))

    this_month_percent = (this_month_remaining / this_month_income * 100) if this_month_income > 0 else 0
    this_month_percent = max(0, min(100, this_month_percent))

    return {
        "total_income": total_income,
        "total_spent": total_spent,
        "transaction_spent": spent_breakdown["transactions"],
        "subscription_spent": spent_breakdown["subscriptions"],
        "remaining": remaining,
        "percent_remaining": round(percent_remaining, 1),
        "is_negative": remaining < 0,
        "this_month": {
            "income": this_month_income,
            "spent": this_month_spent,
            "transaction_spent": this_month_spent_breakdown["transactions"],
            "subscription_spent": this_month_spent_breakdown["subscriptions"],
            "remaining": this_month_remaining,
            "percent_remaining": round(this_month_percent, 1),
            "is_negative": this_month_remaining < 0,
        },
        "period": {
            "month_start": month_start.isoformat(),
            "month_end": month_end.isoformat(),
        }
    }

def compute_income_by_source(user, period_start=None, period_end=None):
    """Get income grouped by source."""
    queryset = Income.objects.filter(user=user)

    if period_start:
        queryset = queryset.filter(period_end__gte=period_start)
    if period_end:
        queryset = queryset.filter(period_start__lte=period_end)

    by_source = queryset.values('source').annotate(
        total=Sum('amount')
    ).order_by('-total')

    return [
        {
            "source": item["source"],
            "total": float(item["total"])
        }
        for item in by_source
    ]

def compute_monthly_income(user, year=None):
    """Get income grouped by month for a specific year."""
    if year is None:
        year = date.today().year
    
    queryset = Income.objects.filter(
        user=user,
        date_receive__year=year
    )

    monthly = queryset.annotate(
        month=TruncMonth('date_received')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')

    monthly_totals = [0] * 12
    for item in monthly:
        if item['month']:
            month_index = item['month'].month -1
            monthly_totals[month_index] = float(item['total'])
    
    return {
        "year": year,
        "months": monthly_totals,
        "total": sum(monthly_totals)
    }

def get_income_with_details(income, user):
    """Get a single income record with computed details including spending."""
    spent_breakdown = compute_total_spent(
        user,
        income.period_start,
        income.period_end
    )

    return {
        "id": income.id,
        "amount": float(income.amount),
        "source": income.source,
        "date_received": income.date_received.isoformat(),
        "period_start": income.period_start.isoformat(),
        "period_end": income.period_end.isoformat(),
        "period_days": (income.period_end - income.period_start).days + 1,
        "daily_rate": float(income.amount) / max(1, (income.period_end - income.period_start).days + 1),
        "spent_in_period": spent_breakdown["total"],
        "transaction_spent": spent_breakdown["transactions"],
        "subscription_spent": spent_breakdown["subscriptions"],
        "remaining_in_period": float(income.amount) - spent_breakdown["total"]
    }

