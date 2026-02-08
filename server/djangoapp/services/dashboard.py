from ..models import Budget, Transaction, Subscription
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from decimal import Decimal
from .date_filter import filter_queryset_by_period
from .spending_calculations import get_subscription_amount_for_period, compute_total_spent
from income import compute_total_income
from category_service import compute_spending_by_category

def compute_dashboard_summary(user, period="monthly"):
    """Compute complete dashboard summary"""
    today = date.today()

    # Determine period boundaries
    if period == "daily":
        period_start = today
        period_end = today
    elif period == "weekly":
        period_start = today - timedelta(days=today.weekday())
        period_end = period_start + timedelta(days=6)
    elif period == "monthly":
        period_start = date(today.year, today.month, 1)
        if today.month == 12:
            period_end = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            period_end = date(today.year, today.month + 1, 1) - timedelta(days=1)
    elif period =="yearly":
        period_start = date(today.year, 1, 1)
        period_end = date(today.year, 12, 31)
    else:
        period_start = None
        period_end = None
    
    # Get spending breakdown
    spent_breakdown= compute_total_spent(user, period_start, period_end)

    # Get income
    total_income = compute_total_income(user, period_start, period_end)

    # Get category breakdown
    categories = compute_spending_by_category(user, period_start, period_end)

    return {
        "period": {
            "type": period,
            "start": period_start.isoformat() if period_start else None,
            "end": period_end.isoformat() if period_end else None,
        },
        "income": {
            "total": total_income,
        },
        "spending": {
            "total": spent_breakdown["total"],
            "transactions": spent_breakdown["transactions"],
            "subscriptions": spent_breakdown["subscriptions"],
        },
        "remaining": total_income - spent_breakdown["total"],
        "categories": categories
    }

