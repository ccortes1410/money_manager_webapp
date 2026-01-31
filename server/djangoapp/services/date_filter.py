from datetime import datetime, timedelta
from django.utils import timezone
from enum import Enum

class Period(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY=  "yearly"
    TOTAL = "total"

    @classmethod
    def from_string(cls, value: str):
        """Safely convery string to Period enum."""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.MONTHLY # Default fallback
        

def get_date_range(period: Period | str) -> dict:
    """
    Returns Django ORM filter kwargs for the given period.

    Usage:
        date_range = get_date_range("monthly")
        transactions = Transaction.objects.filter(**date_range)
    
    Returns:
        dict with 'date_range' and 'date__lte' keys, or empty dict for 'total'
    """

    if isinstance(period, str):
        period = Period.from_string(period)

    now = timezone.now()

    if period == Period.TOTAL:
        return {}
    
    start = _get_period_start(period, now)

    return {
        "date__gte": start,
        "date__lte": now,
    }

def _get_period_start(period: Period, now: datetime) -> datetime:
    """Calculate the start date for a given period."""

    if period == Period.DAILY:
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    elif period == Period.WEEKLY:
        return now - timedelta(days=7)
    
    elif period == Period.MONTHLY:
        return now - timedelta(days=30)
    
    elif period == Period.YEARLY:
        return now - timedelta(days=365)
    
    return now

def get_date_bounds(period: Period | str) -> tuple[datetime | None, datetime | None]:
    """
    Returns (start_date, end_date) tuple.

    Useful when you need the actual dates, not ORM kwargs.

    Usage:
        start, end = get_date_bounds("weekly")
    """
    if isinstance(period, str):
        period = Period.from_string(period)
    
    if period == Period.TOTAL:
        return (None, None)
    
    now = timezone.now()
    start = _get_period_start(period, now)

    return (start, now)

def filter_queryset_by_period(queryset, period: str, date_field: str = "date"):
    """
    Filter any queryset by period using a specified date field.

    Usage:
        transactions = filter_queryset_by_period(
            Transaction.objects.filter(user=user),
            period="monthly",
            date_field="date"
        )

        subscriptions = filer_queryset_by_period(
            Subscription.objects.filer(user=user),
            period="yearly",
            date_field="start_date"
        )
    """
    period_enum = Period.from_string(period)

    if period_enum == Period.TOTAL:
        return queryset
    
    start, end = get_date_bounds(period_enum)

    filter_kwargs = {
        f"{date_field}__gte": start,
        f"{date_field}__lte": end,
    }

    return queryset.filter(**filter_kwargs)


def get_period_label(period: str) -> str:
    """
    Returns human-readable label for the period.

    Usage: 
        label = get_period_label("monthly")  # "Last 30 Days"
    """
    labels = {
        "daily": "Today"
        "weekly" "Last 7 Days",
        "monthly": "Last 30 Days",
        "yearly": "Last Year",
        "total": "All Time"
    }

    return labels.get(period.lower(), "Last 30 Days")


def get_period_display_dates(period: str) -> dict:
    """
    Returns formatted strings for display.

    Usage:
        dates = get_period_display_dates("weekly")
        # { "start": "Jun 01, 2025", "end": "Jun 08, 2025", "label": "Last 7 Days"}
    """
    start, end = get_date_bounds(period)

    return {
        "start": start.strftime("%b %d, %Y") if start else None,
        "end": end.strftime("%b %d, %Y") if end else None,
        "label": get_period_label(period)
    }