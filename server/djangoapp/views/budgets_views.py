import json
import logging
from decimal import Decimal

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..restapi import get_request, post_request, patch_request, delete_request
from ..services.api_adapters import budget_from_row
from ..services.date_filter import get_date_bounds
from ..services.budgets_service import (
    reset_expired_budgets,
    compute_budget_spent,
    get_transactions_for_budget,
    get_subscriptions_for_budget,
    update_budget,
)

logger = logging.getLogger(__name__)

def _iso_date(dt):
    """Normalize a datetime or date into a plain YYYY-MM-DD string."""
    return dt.date().isoformat() if hasattr(dt, "date") else dt.isoformat()


def get_budgets_data(user, period):
    """Get budget summary for dashboard."""
    start, end = get_date_bounds(period)

    budget_params = {"user_id": user.id}
    transaction_params = {"user_id": user.id}

    if start and end:
        budget_params["period_start__gte"] = _iso_date(start)
        budget_params["period_start__lte"] = _iso_date(end)
        transaction_params["date__gte"] = _iso_date(start)
        transaction_params["date__lte"] = _iso_date(end)
    # Get budgets for the period
    budgets = get_request("budgets/", **budget_params) or []
    transactions = get_request("transactions/", **transaction_params) or []

    total_budgeted = sum((Decimal(str(b["amount"])) for b in budgets), Decimal("0"))
    total_spent = sum((Decimal(str(t["amount"])) for t in transactions), Decimal("0"))
    remaining = total_budgeted - total_spent
    percent_used = round(float(total_spent / total_budgeted) * 100, 1) if total_budgeted > 0 else 0

    return {
        "total_budgeted": float(total_budgeted),
        "total_spent": float(total_spent),
        "remaining": float(remaining),
        "percent_used": percent_used,
        "is_over": remaining < 0
    }


def get_budgets(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )

    if request.method != "GET":
        return JsonResponse(
            {"error": "Method Not Allowed"}, status=405
        )
    
    reset_expired_budgets(request.user)

    try:
        rows = get_request("budgets/", user_id=request.user.id) or []
        budgets = [budget_from_row(r) for r in rows if r["is_active"]]
        budgets.sort(key=lambda b: b.period_start, reverse=True)

        budgets_data = []
        for budget in budgets:
            spent_breakdown = compute_budget_spent(budget)
            spent = spent_breakdown["total"]

            budgets_data.append({
                "id": budget.id,
                "category": budget.category,
                "amount": float(budget.amount),
                "period_start": budget.period_start.isoformat(),
                "period_end": budget.period_end.isoformat(),
                "recurrence": budget.recurrence,
                "is_recurring": budget.is_recurring,
                "is_active": budget.is_active,
                "is_shared": budget.is_shared,
                "spent": float(spent),
                "transaction_spent": spent_breakdown["transactions"],
                "subscription_spent": spent_breakdown["subscriptions"],
                "remaining": float(budget.amount) - float(spent),
            })

        return JsonResponse({
            "budgets": budgets_data,
            "user": {
                "id": request.user.id,
                "username": request.user.username,
                "is_authenticated": request.user.is_authenticated,
            },
        })
    except Exception as e:
        logger.error(f"Error fetching budgets: {e}")
        return JsonResponse({"error": "Failed to fetch budget"}, status=500)


def get_budget(request, budget_id):
    """Get a single budget with its transactions and subscriptions."""
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )
    
    if request.method != "GET":
        return JsonResponse({"error": "Method Not Allowed"}, status=405)
    
    row = get_request(f"budgets/{budget_id}")
    # The generic API has no concept of "this user's budgets" -- it will
    # happily return any row for any id. Ownership has to be enforced here.
    if not row or row["user_id"] != request.user.id:
        return JsonResponse({"error": "Budget not found"}, status=404)

    budget = budget_from_row(row)
    spent_breakdown = compute_budget_spent(budget)

    transactions = sorted(
        get_transactions_for_budget(budget), key=lambda t: t.date, reverse=True
    )
    tx_data = [
        {
            "id": t.id,
            "amount": float(t.amount),
            "date": t.date.isoformat(),
            "description": t.description,
            "category": t.category,
            "type": "transaction",
        }
        for t in transactions
    ]

    subscriptions = get_subscriptions_for_budget(budget)
    subs_data = [
        {
            "id": s.id,
            "name": s.name,
            "amount": float(s.amount),
            "billing_cycle": s.billing_cycle,
            "billing_day": s.billing_day,
            "category": s.cateogry,
            "type": "subscription"
        }
        for s in subscriptions
    ]

    budget_data = {
        "id": budget.id,
        "category": budget.category,
        "amount": float(budget.amount),
        "period_start": budget.period_start.isoformat(),
        "period_end": budget.period_end.isoformat() if budget.period_end else None,
        "recurrence": budget.recurrence,
        "is_active": budget.is_active,
        "is_shared": budget.is_shared,
        "spent": spent_breakdown["total"],
        "transaction_spent": spent_breakdown["transactions"],
        "subscription_spent": spent_breakdown["subscriptions"],
        "remaining": float(budget.amount) - float(spent_breakdown["total"]),
        "transactions": tx_data,
        "subscriptions": subs_data,
    }

    return JsonResponse({
        "budget": budget_data,
        "user": {
            "id": request.user.id,
            "username": request.user.username,
            "is_authenticated": request.user.is_authenticated,
        }
    })


@csrf_exempt
def budget_create(request):
    """Create a new budget."""
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error":"Invalid JSON"}, status=400)
    
    required_fields = ["category", "amount", "period_start", "period_end"]
    for field in required_fields:
        if field not in data:
            return JsonResponse({"error":f"Missing field: {field}"}, status=400)
        
    budget = post_request("budgets/", {
        "user_id": request.user.id,
        "category": data["category"],
        "amount": data["amount"],
        "period_start": data["period_start"],
        "period_end": data["period_end"],
        "recurrence": data.get("recurrence", "monthly"),
        "is_recurring": data.get("is_recurring", False),
        "is_active": True,
        "is_shared": data.get("is_shared", False),
    })

    if not row:
        return JsonResponse({"error": "Failed to create budget"}, status=500)

    return JsonResponse({
        "message": "Budget created successfully",
        "budget": {
            "id": row["id"],
            "category": row["category"],
            "amount": row["amount"],
        },
    }, status=201)


@csrf_exempt
@require_http_methods(["PATCH"])
def update_budget_view(request, budget_id):
    """Update budget details."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error":"Invalid JSON"}, status=400)
    
    result = update_budget(budget_id, request.user, data)

    if not result["success"]:
        return JsonResponse({"error": result["error"]}, status=404)

    budget = result["budget"]
    spent = compute_budget_spent(budget)["total"]

    return JsonResponse({
        "message": "Budget updated successfully",
        "budget": {
            "id": budget.id,
            "category": budget.category,
            "amount": float(budget.amount),
            "period_start": budget.period_start.isoformat(),
            "period_end": budget.period_end.isoformat(),
            "recurrence": budget.recurrence,
            "is_recurring": budget.is_recurring,
            "is_active": budget.is_active,
            "is_shared": budget.is_shared,
            "spent": float(spent),
            "remaining": float(budget.amount) - float(spent),
        },
    })


@csrf_exempt
def toggle_recurring(request, budget_id):
    """Toggle budget recurring status."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    if request.method != "PATCH":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error":"Invalid JSON"}, status=400)
    
    row = get_request(f"budgets/{budget_id}")
    if not row or row["user_id"] != request.user.id:
        return JsonResponse({"error": "Budget not found"}, status=404)

    payload = {"is_recurring": data.get("is_recurring", False)}
    if data.get("recurrence"):
        payload["recurrence"] = data["recurrence"]

    updated = patch_request(f"budgets/{budget_id}", payload)
    if not updated:
        return JsonResponse({"error": "Failed to update budget"}, status=500)

    return JsonResponse({
        "message": "Budget recurring status updated",
        "budget": {
            "id": updated["id"],
            "is_recurring": updated["is_recurring"],
            "recurrence": updated["recurrence"],
        },
    })
    
@csrf_exempt
def budget_delete(request, budget_id):
    """Delete a budget"""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    if request.method != "DELETE":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    row = get_request(f"budgets/{budget_id}")
    if not row or row["user_id"] != request.user.id:
        return JsonResponse({"error": "Budget not found"}, status=404)

    delete_request(f"budgets/{budget_id}")
    return JsonResponse({"message": "Budget deleted successfully"})