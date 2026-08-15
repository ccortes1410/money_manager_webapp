from decimal import Decimal
from django.http import JsonResponse
import json
import logging
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from datetime import date, timedelta

from ..restapi import get_request, post_request, patch_request, delete_request
from ..services.date_filter import get_date_bounds
from ..services.api_adapters import income_from_row

logger = logging.getLogger(__name__)

def _iso_date(dt):
    """Normalize a datetime or date into a plain YYYY-MM-DD string."""
    return dt.date().isoformat() if hasattr(dt, "date") else dt.isoformat()


def get_income_data(user, period):
    """Get income vs spending for dashboard."""
    start, end = get_date_bounds(period)

    # Get income for the period
    income_params = {"user_id": user.id}
    if start and end:
        income_params["period_start__gte"] = _iso_date(start)
        income_params["period_start__lte"] = _iso_date(end)
    incomes = get_request("incomes/", **income_params) or []

    # Get all spending (transactions + subscriptions payments)
    transaction_params = {"user_id": user.id}
    if start and end:
        transaction_params["date__gte"] = _iso_date(start)
        transaction_params["date__lte"] = _iso_date(end)
    transactions = get_request("transactions/", **transaction_params) or []

    subscription_payment_params = {"user_id": user.id}
    if start and end:
        subscription_payment_params["due_date__gte"] = _iso_date(start)
        subscription_payment_params["due_date__lte"] = _iso_date(end)
    subscription_payments = get_request("subscription-payments/", **subscription_payment_params) or []

    # Calculate totals
    total_income = sum((Decimal(str(i.amount)) for i in incomes), Decimal('0'))
    transaction_spending = sum((Decimal(str(t["amount"])) for t in transactions), Decimal('0'))
    subscription_spending = sum((Decimal(str(p["amount"])) for p in subscription_payments), Decimal('0'))
    total_spent = transaction_spending + subscription_spending
    remaining = total_income - total_spent

    return {
        "total_income": float(total_income),
        "total_spent": float(total_spent),
        "remaining": float(remaining),
        "percent_remaining": round((remaining / total_income) * 100, 1) if total_income > 0 else 0,
        "is_negative": remaining < 0
    }


def get_incomes(request):
    # Get all income records with summary
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )

    if request.method != "GET":
        return JsonResponse(
            {"error": "Method Not Allowed"}, status=405
        )

    try:
        rows = get_request("incomes/", user_id=request.user.id) or []
        incomes = [income_from_row(r) for r in rows]
        incomes.sort(key=lambda i: i.date_received, reverse=True)

        # Get all transactions and subscription payments for the user (for summary calculation)
        transactions_rows = get_request("transactions/", user_id=request.user.id) or []
        subscription_payment_rows = get_request("subscription-payments/", user_id=request.user.id) or []

        # Calculate summary (all time)
        total_income = sum((Decimal(str(i.amount)) for i in incomes), Decimal('0'))
        total_transaction_spent = sum((Decimal(str(t["amount"])) for t in transactions_rows), Decimal('0'))
        total_subscription_spent = sum((Decimal(str(p["amount"])) for p in subscription_payment_rows), Decimal('0'))
        total_spent = total_transaction_spent + total_subscription_spent
        remaining = total_income - total_spent
        percent_remaining = round((remaining / total_income) * 100, 1) if total_income > 0 else 0
        is_negative = remaining < 0

        summary = {
            "total_income": float(total_income),
            "total_spent": float(total_spent),
            "transaction_spent": float(total_transaction_spent),
            "subscription_spent": float(total_subscription_spent),
            "remaining": float(remaining),
            "percent_remaining": percent_remaining,
            "is_negative": is_negative,
        }

        # Calculate income by source (all time)
        by_source_dict = {}
        for inc in incomes:
            source = inc.source
            amount = Decimal(str(inc.amount))
            by_source_dict[source] = by_source_dict.get(source, Decimal('0')) + amount
        by_source = [{"source": source, "total": float(total)} for source, total in by_source_dict.items()]
        by_source.sort(key=lambda x: x["total"], reverse=True)

        incomes_data = []
        for inc in incomes:
            incomes_data.append({
                "id": inc.id,
                "amount": float(inc.amount),
                "source": inc.source,
                "date_received": inc.date_received,
                "period_start": inc.period_start,
                "period_end": inc.period_end or None,
            })

        return JsonResponse({
            "incomes": incomes_data,
            "summary": summary,
            "by_source": by_source,
            "count": len(incomes_data),
            "user": {
                "id": request.user.id,
                "username": request.user.username,
                "is_authenticated": request.user.is_authenticated
            }
        })
    except Exception as e:
        logger.error(f"Error fetching income: {e}")
        return JsonResponse({"error": "Failed to fetch income"}, status=500)

    
def get_income(request, income_id):
    """Get a single income record with details."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    if request.method != 'GET':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)

    try:
        # Get income record via API
        row = get_request(f"incomes/{income_id}/")
        if not row or row["user_id"] != request.user.id:
            return JsonResponse(
                {"error": "Income not found"}, status=404
            )

        income = income_from_row(row)

        # Get transactions within this income's period via API
        transaction_params = {
            "user_id": request.user.id,
            "date__gte": _iso_date(income.period_start),
            "date__lte": _iso_date(income.period_end)
        }
        transactions_rows = get_request("transactions/", **transaction_params) or []
        transactions = [transaction_from_row(tx) for tx in transactions_rows]
        transactions_data = [
            {
                "id": tx.id,
                "amount": float(tx.amount) if tx.amount else 0,
                "description": tx.description,
                "category": tx.category,
                "date": tx.date.isoformat() if tx.date else None,
                "type": "transaction",
            }
            for tx in transactions
        ]

        # Get subscriptions that apply to this period via API
        subscription_params = {
            "user_id": request.user.id,
            "start_date__lte": _iso_date(income.period_end),
        }
        # For end_date: either null or >= period_start
        # We'll get all active subscriptions and filter in Python for simplicity
        # Alternatively, we could do two calls: one with end_date__isnull=true and one with end_date_gte=period_start
        # But let's get all and filter
        subscription_rows = get_request("subscriptions/", user_id=request.user.id, is_active=True) or []
        filtered_subscriptions = []
        for sub in subscription_rows:
            start_date = sub["start_date"]
            end_date = sub["end_date"]
            if start_date and start_date <= income.period_end.isoformat():
                if end_date is None or end_date >= income.period_start.isoformat():
                    filtered_subscriptions.append(sub)

        subscriptions_data = [
            {
                "id": sub["id"],
                "name": sub["name"],
                "amount": float(sub["amount"]) if sub["amount"] else 0,
                "category": sub["category"],
                "billing_cycle": sub["billing_cycle"],
                "type": "subscription",
            }
            for sub in filtered_subscriptions
        ]

        # Get income details via API (or compute)
        income_details = get_request(f"incomes/{income_id}/details/") or {}
        # If details endpoint doesn't exist, we compute from the income row and spending data
        if not income_details:
            # Calculate spent in period from transactions and subscription payments
            spent_breakdown = get_request("spending/breakdown/",
                                        user_id=request.user.id,
                                        period_start=row["period_start"],
                                        period_end=row["period_end"]) or {}
            income_details = {
                "id": row["id"],
                "amount": float(row["amount"] or 0),
                "source": row["source"],
                "date_received": row["date_received"],
                "period_start": row["period_start"],
                "period_end": row["period_end"],
                "period_days": (row["period_end"] - row["period_start"]).days + 1 if row["period_end"] and row["period_start"] else 0,
                "daily_rate": float(row["amount"]) / max(1, row["period_end"] - row["period_start"].days + 1) if row["period_end"] and row["period_start"] else 0,
                "spent_in_period": spent_breakdown.get("total", 0),
                "transaction_spent": spent_breakdown.get("transactions", 0),
                "subscription_spent": spent_breakdown.get("subscriptions", 0),
                "remaining_in_period": float(row["amount"]) - spent_breakdown.get("total", 0)
            }

        income_details["transactions"] = transactions_data
        income_details["subscriptions"] = subscriptions_data

        return JsonResponse({
            "income": income_details,
            "user": {
                "id": request.user.id,
                "username": request.user.username,
                "is_authenticated": request.user.is_authenticated
            }
        })

    except Exception as e:
        logger.error(f"Error fetching income: {e}")
        return JsonResponse(
            {"error": "Failed to fetch income"}, status=500
        )

def get_income_summary(request):
    """Get income summary only (for dashboard)."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    if request.method != 'GET':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)
    
    try:
        summary = get_request("incomes/summary/", user_id=request.user.id) or []
        by_source = get_request("incomes/by-source/", user_id=request.user.id) or []

        current_year = date.today().year
        monthly = get_request(f"incomes/monthly/?year={current_year}", user_id=request.user.id)

        return JsonResponse({
            "summary": summary,
            "by_source": by_source,
            "monthly": monthly,
            "user": {
                "id": request.user.id,
                "username": request.user.username,
                "is_authenticated": request.user.is_authenticated
            }
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def income_create(request):
    """Create a new income record."""
    if not request.user.is_authenticated:
        return JsonResponse({
            "error": "Unauthorized"
        }, status=401)
    
    if request.method != 'POST':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    required_fields = ["amount", "source", "date_received", "period_start", "period_end"]
    for field in required_fields:
        if field not in data:
            return JsonResponse({"error": f"Missing field: {field}"}, status=400)
        
    if data["period_end"] < data["period_start"]:
        return JsonResponse({"error": "Period end cannot be before period start"}, status=400)

    # Create via API
    row = post_request("incomes/", {
        "user_id": request.user.id,
        "amount": data["amount"],
        "source": data["source"],
        "date_received": data["date_received"],
        "period_start": data["period_start"],
        "period_end": data["period_end"],
    })

    if not row:
        return JsonResponse(
            {"error": "Failed to create income"}, status=500
        )

    # Get updated summary
    summary = get_request("incomes/summary/", user_id=request.user.id) or {}

    return JsonResponse({
        "message": "Income created successfully",
        "income": {
            "id": row["id"],
            "amount": float(row["amount"]),
            "source": row["source"],
        },
        "summary": summary,
    }, status=201)


@csrf_exempt
def income_update(request, income_id):
    """Update an income record."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    if request.method != "PATCH":
        return JsonResponse({"error": "Method Not Allowed"}, status=405)
    
    try:
        # Verify ownership first
        income_row = get_request(f"incomes/{income_id}/")
        if not income_row or income_row["user_id"] != request.user.id:
            return JsonResponse(
                {"error": "Income not found"}, status=404
            )

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON"}, status=400
            )
        

        allowed_fields = ["amount", "source", "date_received", "period_start", "period_end"]
        payload = {}
        for field in allowed_fields:
            if field in data:
                payload[field] = data[field]

        if not payload:
            return JsonResponse(
                {"error": "No valid fields to update"}, status=400
            )

        if "period_end" in payload and "period_start" in payload:
            if payload["period_end"] < payload["period_start"]:
                return JsonResponse(
                    {"error": "Period end cannot be before period start"}, status=400
                )
        elif "period_end" in payload:
            if payload["period_end"] < income_row["period_start"]:
                return JsonResponse(
                    {"error": "Period end cannot be before period start"}, status=400
                )
        elif "period_start" in payload:
            if income_row["period_end"] < payload["period_start"]:
                return JsonResponse(
                    {"error": "Period end cannot be before period start"}, status=400
                )

        # Update via API
        updated = patch_request(f"incomes/{income_id}/", payload)
        if not updated:
            return JsonResponse(
                {"error": "Failed to update income"}, status=500
            )

        # Get updated summary
        summary = get_request("incomes/summary/", user_id=request.user.id) or {}

        return JsonResponse({
            "message": "Income updated successfully",
            "income": updated,
            "summary": summary,
            "user": {
                "id": request.user.id,
                "username": request.user.username,
                "is_authenticated": request.user.is_authenticated,
            }
        })
    except Exception as e:
        logger.error(f"Error updating income: {e}")
        return JsonResponse(
            {"error": str(e)}, status=400
        )


@csrf_exempt
def income_delete(request):
    """Delete one or more income records."""
    if not request.user.is_authenticated:
        return JsonResponse({
            "error": "Unauthorized"
        }, status=401)
    
    if request.method != 'DELETE':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    income_ids = data.get("income_ids", [])
    if not income_ids:
        return JsonResponse({"error": "No ncome IDs provided"})
    
    # Verify each income belongs to the user before deleting
    for iid in income_ids:
        row = get_request(f"incomes/{iid}/")
        if not row or row["user_id"] != request.user.id:
            return JsonResponse(
                {"error": f"Income {iid} not found or access denied"}, status=404
            )

    # Delete each income
    deleted_count = 0
    for iid in income_ids:
        result = delete_request(f"incomes/{iid}/")
        if result is not None:
            deleted_count += 1

    # Get updated summary
    summary = get_request("incomes/summary/", user_id=request.user.id) or {}

    return JsonResponse({
        "message": f"Deleted {deleted_count} income record(s).",
        "deleted_count": deleted_count,
        "summary": summary,
        "user": {
            "id": request.user.id,
            "username": request.user.username,
            "is_authenticated": request.user.is_authenticated
        }
    })