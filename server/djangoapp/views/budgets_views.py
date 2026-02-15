from ..models.models import Budget, Transaction
from django.db.models import Sum
from django.http import JsonResponse
import json
import logging
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..services.category_service import filter_queryset_by_period
from ..services.budgets import (
    reset_expired_budgets,
    compute_budget_spent,
    get_transactions_for_budget,
    get_subscriptions_for_budget
)

logger = logging.getLogger(__name__)



def get_budgets_data(user, period):
    """Get budget summary for dashboard."""

    # Get budgets for the period
    budgets = filter_queryset_by_period(
        Budget.objects.filter(user=user),
        period=period,
        date_field="period_start"
    )

    transactions = filter_queryset_by_period(
        Transaction.objects.filter(user=user),
        period=period,
        date_field="date"
    )

    # Calculate totals
    total_budgeted = float(budgets.aggregate(total=Sum("amount"))["total"]or 0)
    total_spent = float(transactions.aggregate(total=Sum("amount"))["total"] or 0)
    remaining = total_budgeted - total_spent
    percent_used = round((total_spent / total_budgeted) * 100,1) if total_budgeted > 0 else 0

    return {
        "total_budgeted": total_budgeted,
        "total_spent": total_spent,
        "remaining": remaining,
        "percent_used": percent_used,
        "is_over": remaining < 0
    }


def get_budgets(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )
    
    reset_expired_budgets(request.user)

    budgets = Budget.objects.filter(
        user=request.user,
        is_active=True).order_by('-period_start')
    
    budgets_data = []

    if request.method == "GET":
        try:
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
                    "subscription_spent" : spent_breakdown["subscriptions"],
                    "remaining": float(budget.amount) - float(spent),
                })
            print(budgets_data)
            return JsonResponse({
                "budgets": budgets_data,
                "user": {
                    "id": request.user.id,
                    "username": request.user.username,
                    "is_authenticated": request.user.is_authenticated
                }
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
    
    try:
        budget = Budget.objects.get(id=budget_id, user=request.user)
    except Budget.DoesNotExist:
        return JsonResponse({"error": "Budget not found"}, status=404)
    
    spent_breakdown = compute_budget_spent(budget)

    transactions = get_transactions_for_budget(budget).order_by('-date')

    tx_data = [
        {
            "id": t.id,
            "amount": float(t.amount),
            "date": t.date.isoformat(),
            "description": t.description,
            "category": t.category,
            "type": "transaction"
        }
        for t in transactions
    ]

    subscriptions = get_subscriptions_for_budget(budget)
    subs_data = [
        {
            "id": sub.id,
            "name": sub.name,
            "amount": float(sub.amount),
            "billing_cycle": sub.billing_cycle,
            "billing_day": sub.billing_day,
            "category": sub.category,
            "type": "subscription",
        }
        for sub in subscriptions
    ]

    budget_data = {
        "id": budget.id,
        "category": budget.category,
        "amount": float(budget.amount),
        "period_start": budget.period_start.isoformat(),
        "period_end": budget.period_end.isoformat() if budget.period_end else None,
        "recurrence": budget.recurrence,
        "is_active": budget.is_active,
        "is_recurring": budget.is_recurring,
        "is_shared": budget.is_shared,
        "spent": spent_breakdown["total"],
        "transaction_spent": spent_breakdown["transactions"],
        "subscriptions_spent": spent_breakdown["subscriptions"],
        "remaining": float(budget.amount) - float(spent_breakdown["total"]),
        "transactions": tx_data,
        "subscriptions": subs_data
    }

    logger.debug(f"Budget details: {budget_data}")
    return JsonResponse({
        "budget": budget_data,
        "user": {
            "id": request.user.id,
            "username": request.user.username,
            "is_authenticated": request.user.is_authenticated
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
        
    budget = Budget.objects.create(
        user=request.user,
        category=data["category"],
        amount=data["amount"],
        period_start=data["period_start"],
        period_end=data["period_end"],
        recurrence=data.get("recurrence", "monthly"),
        is_recurring=data.get("is_recurring", False),
        is_active=True,
        is_shared=data.get("is_shared", False),
    )

    return JsonResponse({
        "message": "Budget created successfully",
        "budget": {
            "id": budget.id,
            "category": budget.category,
            "amount": budget.amount,
        }
    }, status =201)


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
    
    from ..services.budgets import update_budget
    result = update_budget(budget_id, request.user, data)

    if result["success"]:
        budget = result["budget"]
        spent = compute_budget_spent(budget)
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
                "remaining": float(budget.amount - spent),
            }
        })
    return JsonResponse({
        "id": budget.id,
        "is_recurring": budget.is_recurring,
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
    
    is_recurring = data.get("is_recurring", False)
    recurrence = data.get("recurrence")

    try:
        budget = Budget.objects.get(id=budget_id, user=request.user)
        budget.is_recurring = is_recurring

        if recurrence:
            budget.recurrence = recurrence

        budget.save(update_fields=["is_recurring", "recurrence"])

        return JsonResponse({
            "message": "Budget recurring status updated",
            "budget": {
                "id": budget.id,
                "is_recurring": budget.is_recurring,
                "recurrence": budget.recurrence,
            }
        })
    except Budget.DoesNotExist:
        return JsonResponse({"error": "Budget not found"}, status=404)
    
@csrf_exempt
def budget_delete(request, budget_id):
    """Delete a budget"""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    if request.method != "DELETE":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        budget = Budget.objects.get(id=budget_id, user=request.user)
        budget.delete()
        return JsonResponse({"message": "Budget deleted successfully"})
    except Budget.DoesNotExist:
         return JsonResponse({"error": "Budget not found"}, status=404)