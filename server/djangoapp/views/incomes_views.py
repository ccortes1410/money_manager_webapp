from ..models.models import Income, Transaction, SubscriptionPayment, Subscription
from datetime import date
from django.db.models import Sum, Q
from django.http import JsonResponse
import json
import logging
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..services.category_service import filter_queryset_by_period
from ..services.income import (
    compute_income_by_source,
    compute_income_summary,
    get_income_with_details,
    compute_monthly_income
)

logger = logging.getLogger(__name__)

def get_income_data(user, period):
    """Get income vs spending for dashboard."""

    # Get income for the period
    income = filter_queryset_by_period(
        Income.objects.filter(user=user),
        period=period,
        date_field="period_start"
    )

    # Get all spending (transactions + subscriptions payments)
    transactions = filter_queryset_by_period(
        Transaction.objects.filter(user=user),
        period=period,
        date_field="date"
    )

    subscription_payments = filter_queryset_by_period(
        SubscriptionPayment.objects.filter(subscription__user=user),
        period=period,
        date_field="date"
    )

    # Calculate totals
    total_income = float(income.aggregate(total=Sum("amount"))["total"] or 0)
    transaction_spending = float(transactions.aggregate(total=Sum("amount"))["total"] or 0)
    subscription_spending = float(subscription_payments.aggregate(total=Sum("amount"))["total"] or 0)
    total_spent = transaction_spending + subscription_spending
    remaining = total_income - total_spent

    return {
        "total_income": total_income,
        "total_spent": total_spent,
        "remaining": remaining,
        "percent_remaining": round((remaining / total_income) * 100, 1) if total_income > 0 else 0,
        "is_negative": remaining < 0
    }


def get_incomes(request):
    # Get all income records with summary
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )
    
    if request.method == "GET":
        try:
            incomes = Income.objects.filter(user=request.user).order_by('date_received')

            # Get summary calculations (includes transactions + subscriptions)
            summary = compute_income_summary(request.user)
            by_source = compute_income_by_source(request.user)
            print("Income by source:", by_source)
            incomes_data = [
                {
                    "id": inc.id,
                    "amount": float(inc.amount),
                    "source": inc.source,
                    "date_received": inc.date_received.isoformat(),
                    "period_start": inc.period_start.isoformat(),
                    "period_end": inc.period_end.isoformat() or None,
                }
                for inc in incomes
            ]
            # print("Income data:", incomes_data)
            # print("Income summary:", summary)
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
    if not request.user.is_authenticate:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    if request.method != 'GET':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)
    
    try:
        income = Income.objects.get(id=income_id, user=request.user)
    except Income.DoesNotExist:
        return JsonResponse({"erorr": "Income not found"}, status=404)
    
    # Get transactions within this income's period
    transactions = Transaction.objects.filter(
        user=request.user,
        date__gte=income.period_start,
        date__lte=income.period_end,
    ).order_by('-date')

    # Get subscriptions that apply to this period
    subscriptions = Subscription.objects.filter(
        user=request.user,
        is_active=True,
        start_date__lte=income.period_end
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=income.period_start)
    )

    transactions_data = [
        {
            "id": tx.id,
            "amount": float(tx.amount),
            "description": tx.description,
            "category": tx.category,
            "date": tx.date.isoformat(),
            "type": "transaction",
        }
        for tx in transactions
    ]

    subscriptions_data = [
        {
            "id": sub.id,
            "name": sub.name,
            "amount": float(sub.amount),
            "category": sub.category,
            "billing_cycle": sub.billing_cycle,
            "type": "subscription",
        }
        for sub in subscriptions
    ]

    income_data = get_income_with_details(income, request.user)
    income_data["transactions"] = transactions_data,
    income_data["subscriptions"] = subscriptions_data
    
    return JsonResponse({
        "income": income_data,
        "user": {
            "id": request.user.id,
            "username": request.user.username,
            "is_authenticated": request.user.is_authenticated
        }
        })

def get_income_summary(request):
    """Get income summary only (for dashboard)."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    if request.method != 'GET':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)
    
    try:
        summary = compute_income_summary(request.user)
        by_source = compute_income_by_source(request.user)

        current_year = date.today().year
        monthly = compute_monthly_income(request.user, current_year)

        return JsonResponse({
            "summary": summary,
            "by_source": by_source,
            "monthly": monthly,
            "user": {
                "id": request.user.id,
                "username": request.user.username,
                "is_authentincated": request.user.is_authenticated
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
    
    income = Income.objects.create(
        user=request.user,
        amount=data["amount"],
        source=data["source"],
        date_received=data["date_received"],
        period_start=data["period_start"],
        period_end=data["period_end"],
    )

    summary = compute_income_summary(request.user)

    return JsonResponse({
        "message": "Income created succesfully",
        "income": {
            "id": income.id,
            "amount": float(income.amount),
            "source": income.source,
        },
        "summary": summary,
    }, status=201)

@csrf_exempt
def income_update(request, income_id):
    """Update an income record."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    if request.metho != 'PATCH':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)
    
    try:
        income = Income.objects.get(id=income_id, user=request.user)
    except Income.DoesNotExist:
        return JsonResponse({"error": "Income not found"}, status=404)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    allowed_fields = ["amount", "source", "date_received", "period_start", "period_end"]
    for field in allowed_fields:
        if field in data:
            setattr(income, field, data[field])
        
    if income.period_end < income.period_start:
        return JsonResponse({"error": "Period end cannot be before period start"}, status=400)
    
    income.save()

    summary = compute_income_summary(request.user)

    return JsonResponse({
        "message": "Income updated succesfully",
        "income": get_income_with_details(income, request.user),
        "summary": summary,
        "user": {
            "id": request.user.id,
            "username": request.user.username,
            "is_authenticated": request.user.is_authenticated,
        }
    })

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
        return JsonResponse({"error": "No income Income IDs provided"})
    
    deleted_count = Income.objects.filter(
        id__in=income_ids,
        user=request.user
    ).delete()[0]

    summary = compute_income_summary(request.user)

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