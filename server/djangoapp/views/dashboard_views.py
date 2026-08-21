
from django.http import JsonResponse
import json
import logging
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from collections import defaultdict

from .budgets_views import get_budgets_data
from .incomes_views import get_income_data

from ..restapi import get_request, post_request, patch_request, delete_request
from ..services.date_filter import get_date_bounds, get_period_label, get_period_display_dates
from ..services.api_adapters import (
    transaction_from_row,
    subscription_from_row,
    subscription_payment_from_row,
    get_username,
    get_user_first_name,
    get_user_last_name,
    get_user_email,
    get_user_data
)

logger = logging.getLogger(__name__)

def _iso_date(dt):
    """Normalize a datetime or date into a plain YYYY-MM-DD string."""
    return dt.date().isoformat() if hasattr(dt, "date") else dt.isoformat()

def _group_daily(transactions):
    """Single bar for today"""
    today = timezone.now().date()
    total = sum((Decimal(str(t["amount"])) for t in transactions if t["date"] == today.isoformat()), Decimal('0'))
    return [{
        "label": "Today",
        "date": today.isoformat(),
        "total": float(total)
    }]

def _group_by_day(transactions, days: int):
    """Group by each day for the last N days"""
    today = timezone.now().date()
    start_date = today - timedelta(days=days - 1)

    # Create lookup dict for totals by date
    data_by_date = defaultdict(Decimal)
    for t in transactions:
        if t["date"]:
            data_by_date[t["date"]] += Decimal(str(t["amount"]))

    result = []
    current = start_date
    while current <= today:
        date_str = current.isoformat()
        result.append({
            "label": current.strftime("%b %d"),
            "date": date_str,
            "total": float(data_by_date.get(date_str, 0))
        })
        current += timedelta(days=1)

    return result

def _group_by_month(transactions):
    """Group by each month for the last 12 months"""
    today = timezone.now().date()

    # Create lookup dict for totals by month (year-month)
    data_by_month = defaultdict(Decimal)
    for t in transactions:
        if t["date"]:
            try:
                date_obj = datetime.fromisoformat(t["date"]).date()
                month_key = (date_obj.year, date_obj.month)
                data_by_month[month_key] += Decimal(str(t["amount"]))
            except ValueError:
                pass

    result = []
    for i in range(11, -1, -1):
        year = today.year
        month = today.month - i
        # Adjust for negative months
        while month <= 0:
            month += 12
            year -= 1

        month_date = datetime(year, month, 1).date()
        month_key = (year, month)
        total = data_by_month.get(month_key, 0)

        result.append({
            "label": month_date.strftime("%b"),
            "date": month_date.isoformat(),
            "total": float(total)
        })

    return result

def _group_by_year(transactions):
    """Group by each year"""
    # Create lookup dict for totals by year
    data_by_year = defaultdict(Decimal)
    for t in transactions:
        if t["date"]:
            try:
                date_obj = datetime.fromisoformat(t["date"]).date()
                year_key = date_obj.year
                data_by_year[year_key] += Decimal(str(t["amount"]))
            except ValueError:
                pass

    result = []
    for year, total in sorted(data_by_year.items(), reverse=True):
        result.append({
            "label": str(year),
            "date": f"{year}-01-01",
            "total": float(total)
        })

    return result

def get_transactions_chart_data(user, period: str):
    """
    Returns transactions grouped by appropriate time granularity (chart data).
    Mirrors the logic from the original service but uses API calls.
    """
    # Get raw transactions data from API
    transaction_params = {"user_id": user.id}

    # We'll get all transactions and filter by period in Python for simplicity
    # In a production app, you might want to add date filtering to the API call
    transactions = get_request("transactions/", **transaction_params) or []

    if period == "daily":
        return _group_daily(transactions)
    elif period == "weekly":
        return _group_by_day(transactions, days=7)
    elif period == "monthly":
        return _group_by_day(transactions, days=30)  # Approximate month
    elif period == "yearly":
        return _group_by_year(transactions)
    elif period == "total":
        return _group_by_year(transactions)  # Group by year for total view
    else:
        # Default to monthly
        return _group_by_day(transactions, days=30)

def compute_spending_by_category(user, period: str):
    """
    Combines transactions and subscription payments by category.
    Mirrors the logic from the original service but uses API calls.
    """
    # Get date bounds for filtering
    start, end = get_date_bounds(period)

    # Initialize category totals
    category_totals = defaultdict(lambda: {
        "transactions": 0.0,
        "subscriptions": 0.0,
        "total": 0.0
    })

    # Get transactions for the period
    transaction_params = {"user_id": user.id}
    if start and end:
        transaction_params["date__gte"] = _iso_date(start)
        transaction_params["date__lte"] = _iso_date(end)
    transactions = get_request("transactions/", **transaction_params) or []

    # Process transactions by category
    for t in transactions:
        category = t.get("category") or "Uncategorized"
        amount = float(t.get("amount", 0))
        category_totals[category]["transactions"] += amount
        category_totals[category]["total"] += amount

    # Get subscription payments for the period
    payment_params = {"user_id": user.id}
    if start and end:
        payment_params["due_date__gte"] = _iso_date(start)
        payment_params["due_date__lte"] = _iso_date(end)
    subscription_payments = get_request("subscription-payments/", **payment_params) or []

    # Process subscription payments by category (need to get subscription details)
    # For now, we'll use a default category since we don't have easy access to subscription category
    # In a full implementation, we might need to fetch subscriptions to get their categories
    for p in subscription_payments:
        # Try to get subscription details to get category
        subscription_id = p.get("subscription")
        if subscription_id:
            subscription_row = get_request(f"subscriptions/{subscription_id}")
            if subscription_row:
                category = subscription_row.get("category") or "Uncategorized"
            else:
                category = "Uncategorized"
        else:
            category = "Uncategorized"

        amount = float(p.get("amount", 0))
        category_totals[category]["subscriptions"] += amount
        category_totals[category]["total"] += amount

    # Calculate grand total and percentages
    grand_total = sum(cat["total"] for cat in category_totals.values())

    result = []
    for category, data in category_totals.items():
        result.append({
            "category": category,
            "total": data["total"],
            "transactions": data["transactions"],
            "subscriptions": data["subscriptions"],
            "percentage": round((data["total"] / grand_total) * 100, 1) if grand_total > 0 else 0
        })

    # Sort by total descending
    result.sort(key=lambda x: x["total"], reverse=True)

    return {
        "categories": result,
        "total": grand_total,
        "transaction_total": sum(cat["transactions"] for cat in result),
        "subscription_total": sum(cat["subscriptions"] for cat in result)
    }

def dashboard(request):
    # print(request.user)
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )

    period = request.GET.get("period", "monthly")

    if request.method == "GET":
        try:
            # Get transactions chart data via API
            transactions = get_transactions_chart_data(request.user, period)

            # Get spending by category via API
            categories = compute_spending_by_category(request.user, period)

            # Generate subscription payments (side effect to keep data current)
            # Try to call via API if endpoint exists, otherwise skip
            try:
                post_request("subscription-payments/generate", {"user_id": request.user.id})
            except Exception:
                # If API endpoint doesn't exist, continue without generating payments
                # This maintains backward compatibility
                pass

            # Get subscriptions data via API
            subscription_params = {"user_id": request.user.id, "status": "active"}
            start, end = get_date_bounds(period)
            if start and end:
                subscription_params["start_date__lte"] = _iso_date(end)  # Started before or during period
                subscription_params["end_date__gte"] = _iso_date(start)  # Ends after or during period (or NULL)
            subscriptions = get_request("subscriptions/", **subscription_params) or []

            # Get budgets data (already API-based via local view)
            budgets = get_budgets_data(request.user, period)

            # Get income data (already API-based via local view)
            income = get_income_data(request.user, period)

            return JsonResponse({
                "dashboard": {
                    "transactions": transactions,
                    "categories": categories,
                    "subscriptions": subscriptions,
                    "budgets": budgets,
                    "income": income,
                    "period": {
                        "value": period,
                        "label": get_period_label(period),
                        **get_period_display_dates(period)
                    },
                },
                "user": {
                    "id": request.user.id,
                    "username": request.user.username,
                    "is_authenticated": request.user.is_authenticated
                }
            })
        except Exception as e:
            logger.error(f"Error fetching dashboard: {e}")
            return JsonResponse({"error": "Failed to fetch dashboard"}, status=500)