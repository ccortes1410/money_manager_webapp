from django.db.models import Sum, Count
from django.db.models.functions import TruncDate, TruncMonth, TruncYear
from django.utils import timezone
from datetime import timedelta
from .date_filter import filter_queryset_by_period, Period
from ..models import Transaction


def get_transactions_chart_data(user, period: str):
    """
    Returns transactions grouped by appropiate time granularity.

    - daily: single total for today
    - weekly: 7 days, daily totals
    - monthly: ~30 days, daily totals
    - yearly: 12 months, monthly totals
    - total: all years, yearly totals
    """

    transactions = filter_queryset_by_period(
        Transaction.objects.filter(user=user),
        period=period,
        date_field="date"
    )

    if period == "daily":
        return _group_daily(transactions)
    elif period == "weekly":
        return _group_by_day(transactions, days=7)
    elif period == "monthly":
        return _group_by_day(transactions, days=31)
    elif period == "yearly":
        return _group_by_month(transactions)
    elif period == "total":
        return _group_by_year(transactions)
    else:
        return _group_by_day(transactions, days=31)
    
def _group_daily(transactions):
    """Single bar for today"""
    today = timezone.now().date()
    total = transactions.filter(date=today).aggregate(
        total=Sum("amount")
    )["total"] or 0

    return [{
        "label": "Today",
        "date": today.isoformat(),
        "total": float(total)
    }]

def _group_by_day(transactions, days: int):
    """Group by each y for the last N days"""
    today = timezone.now().date()
    start_date = today - timedelta(days=days - 1)

    # Get data
    grouped = transactions.annotate(
        day=TruncDate("date")
    ).values("day").annotate(
        total=Sum("amount")
    ).order_by("day")

    # Create lookup dict
    data_by_date = {
        item["day"]: float(item["total"])
        for item in grouped
    }

    result = []
    current = start_date
    while current <= today:
        result.append({
            "label": current.strftime("%b %d"),
            "date": current.isoformat(),
            "total": data_by_date.get(current, 0)
        })
        current += timedelta(days=1)
    
    return result

def _group_by_month(transactions):
    """Group by each month for the last 12 months"""
    today = timezone.now().date()

    grouped = transactions.annotate(
        month=TruncMonth("date")
    ).values("month").annotate(
        total=Sum("amount")
    ).order_by("month")


    data_by_month = {
        item["month"]: float(item["total"])
        for item in grouped
    }

    result = []
    for i in range(11, -1, -1):
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1

        month_date = today.replace(year=year, month=month, day=1)

        total = 0
        for key, value in data_by_month.items():
            if key and key.year == year and key.month == month:
                total = value
                break

        result.append({
            "label": month_date.strftime("%b"),
            "date": month_date.isoformat(),
            "total": total
        })
    return result

def _group_by_year(transactions):
    """Group by each year"""
    grouped = transactions.annotate(
        year=TruncYear("date")
    ).values("year").annotate(
        total=Sum("amount")
    ).order_by("year")

    return [
        {
            "label": str(item["year"].year) if item["year"] else "Unknown",
            "date": item["year"].isoformat() if item["year"] else None,
            "total": float(item["total"]) or 0
        }
        for item in grouped
    ]



