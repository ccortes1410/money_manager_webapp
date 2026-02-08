from django.forms import model_to_dict
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import Sum, Q
from .models import Transaction, Budget, Subscription, SubscriptionPayment, Income
from django.contrib.auth.models import User
from django.http import JsonResponse
import json
from datetime import datetime, date, timezone
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .restapi import get_request
from .services.budgets import (
    reset_expired_budgets,
    compute_budget_spent,
    get_transactions_for_budget,
    update_budget,
    get_subscriptions_for_budget
)
from .services.date_filter import (
    filter_queryset_by_period,
    get_period_label,
    get_period_display_dates
)
from .services.transactions import get_transactions_chart_data
from .services.category_service import compute_spending_by_category
from .services.subscription_service import (
    get_subscriptions_for_period,
    compute_subscription_summary,
    compute_subscription_total
    )
from .services.income import (
        compute_income_by_source,
        compute_income_summary,
        compute_monthly_income,
        get_income_with_details,
        compute_total_spent
    )
import logging

logger = logging.getLogger(__name__)

# ======================= AUTH VIEWS ======================= #
def register_user(request):
    context = {}
    if request.method == "GET":
        return render(request, "money_manager/user_registration_bootstrap.html", context)
    elif request.method == "POST":
        try:
            # Accept both JSON and form-encoded POSTs
            if request.META.get("CONTENT_TYPE", "").startswith("application/json"):
                data = json.loads(request.body or b"{}")
                username = data.get("username")
                password = data.get("password")
                first_name = data.get("first_name")
                last_name = data.get("last_name")
                email = data.get("email")
            else:
                username = request.POST.get("username")
                password = request.POST.get("password")
                first_name = request.POST.get("first_name")
                last_name = request.POST.get("last_name")
                email = request.POST.get("email")

            if not username or not password:
                return JsonResponse({"error": "username and password are required"}, status=400)

            if User.objects.filter(username=username).exists():
                return JsonResponse({"error": "Already Registered"}, status=400)

            user = User.objects.create_user(
                username=username,
                first_name=first_name or "",
                last_name=last_name or "",
                email=email or "",
                password=password,
            )
            user.save()
            logger.info(f"User registered: {username}")
            return JsonResponse({"status": True, "userName": username}, status=201)
        except Exception as e:
            logger.exception(f"Error registering user: {e}")
            return JsonResponse({"error": "Failed to register user"}, status=500)

    return render(request, "register.html")

@csrf_exempt
def login_request(request):
    
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    
    try:
        res = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)
    
    username = res.get("username")
    password =  res.get("password")

    print("LOGIN ATTEMPT:", username, password)
    user = authenticate(
        request,
        username=res.get("username"),
        password=res.get("password"),
    )

    if user is not None:
        login(request, user)
        return JsonResponse({
            "username": user.username,
            "is_authenticated": True,
            "id": user.id,
        })

    return JsonResponse({"error": "Invalid username or password"}, status=401)

@csrf_exempt
def logout_request(request):

    logout(request)
    
    return JsonResponse({"status": "logged_out"})


def current_user(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )
    
    return JsonResponse({
        "user": {
            "id": request.user.id,
            "username": request.user.username,
            "is_authenticated": request.user.is_authenticated
            }
        })

# ========================== DASHBOARD VIEW ======================= #
def dashboard(request):
    # print(request.user)
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )

    period = request.GET.get("period", "monthly")

    if request.method == "GET":
        try:
            # transactions = filter_queryset_by_period(
            #         Transaction.objects.filter(user=request.user),
            #         period=period,
            #         date_field="date"
            # )

            transactions = get_transactions_chart_data(request.user, period)

            categories = compute_spending_by_category(request.user, period)

            from .services.subscription_service import generate_subscription_payments
            generate_subscription_payments(request.user)

            subscriptions = get_subscriptions_for_period(request.user, period)

            budgets = get_budgets_data(request.user, period)

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
    

# ====================== TRANSACTIONS VIEW ========================= # 
def transaction_list(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )
    
    category = request.GET.get("category")

    if request.method == "GET":
        if category:
            transactions = Transaction.objects.filter(user=request.user, category=category)
        else:
            transactions = Transaction.objects.filter(user=request.user)
        data = list(transactions.values())
        return JsonResponse({
            "transactions": data,
            "user": {
                "id": request.user.id,
                "username": request.user.username,
                "is_authenticated": request.user.is_authenticated
            }
        })
    
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            amount = data.get("amount")
            date = data.get("date")
            description = data.get("description")
            category = data.get("category")
            Transaction.objects.create(
                user=request.user,
                description=description,
                amount=amount,
                date=date,
                category=category
            )
            return JsonResponse({"status": "Transaction added successfully"}, status=201)
        except Exception as e:
            logger.error(f"Error adding transaction: {e}")
            return JsonResponse({"error": "Failed to add transaction"}, status=500)
    
    elif request.method == "DELETE":
        try:
            data = json.loads(request.body)
            ids = data.get("ids", [])
            Transaction.objects.filter(id__in=ids, user=request.user).delete()
            return JsonResponse({"status": "deleted"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

# ========================= BUDGETS VIEWS ========================= #
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


def get_budgets(request, budget_id=None):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )
    
    reset_expired_budgets(request.user)

    budgets = Budget.objects.filter(
        user=request.user,
        is_active=True).order_by('-period_start')
    
    budgets_data = []
    print(budgets)
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
                    "remaining": float(budget.amount - spent),
                })
            
            return JsonResponse({
                "budgets": budgets_data,
                "user": {
                    "id": request.user.id,
                    "username": request.user.username,
                    "is_authenticated": request.user.is_authenticated
                }
            })  
        except Exception as e:
            logger.error(f"Error fetching budget: {e}")
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
            "categorry": t.category,
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
        "remaining": float(budget.amount) - spent_breakdown["total"],
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
    
    from .services.budgets import update_budget
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

# ============================ SUBSCRIPTIONS VIEWS ====================== #
def subscriptions_list(request):
    """GET: List allsubscriptions for user"""
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )
    
    subscriptions = Subscription.objects.filter(user=request.user).order_by('-created_at')

    data = []
    try:
        if request.method == "GET":
            for sub in subscriptions:
                recent_payments = sub.payments.order_by('-date')[:5]

                data.append({
                    "id": sub.id,
                    "name": sub.name,
                    "amount": float(sub.amount),
                    "category": sub.category,
                    "billing_cycle": sub.billing_cycle,
                    "billing_day": sub.billing_day,
                    "start_date": sub.start_date.isoformat() if sub.start_date else None,
                    "end_date": sub.end_date.isoformat() if sub.end_date else None,
                    "status": sub.status,
                    "description": sub.description,
                    "created_at": sub.created_at.isoformat(),
                    "payments": [
                        {
                            "id": p.id,
                            "amount": float(p.amount),
                            "date": p.date.isoformat(),
                            "is_paid": p.is_paid,
                        }
                        for p in recent_payments
                    ],
                    "total_paid": float(sub.payments.filter(is_paid=True).aggregate(
                        total=Sum('amount'))['total'] or 0
                    ),
                    "payment_count": sub.payments.count()
                })
            return JsonResponse({
                "subscriptions": data,
                "user": {
                    "id": request.user.id,
                    "username": request.user.username,
                    "is_authenticated": request.user.is_authenticated
                }
            })
        
        elif request.method == "POST":
            data = json.loads(request.body)
            name = data.get("name")
            amount = data.get("amount")
            category = data.get("category")
            billing_cycle = data.get("billing_cycle")
            billing_day = data.get("billing_day")
            start_date = data.get("start_date")

            Subscription.objects.create(
                user=request.user,
                name=name,
                amount=amount,
                category=category,
                billing_cycle=billing_cycle,
                billing_day=billing_day,
                start_date=start_date
            )
            return JsonResponse({"status": "Subscription added successfully"}, status=201)   
                  
    except Exception as e:
        logger.error(f"Error fetching subscriptions: {e}")
        return JsonResponse({"error": "Failed to fetch subscriptions"}, status=500)
    return render(request, "money_manager/subscriptions.html")

@csrf_exempt
def subscriptions_detail(request, subscription_id):
    """GET: Single subscription with all payments"""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    try:
        subscription = Subscription.objects.get(id=subscription_id, user=request.user)
    except Subscription.DoesNotExist:
        return JsonResponse({"error": "Subscription not found"}, status=404)
    
    payments = subscription.payments.order_by('-date')

    return JsonResponse({
        "subscription": {
            "id": subscription.id,
            "name": subscription.name,
            "amount": subscription.amount,
            "category": subscription.category,
            "billing_cycle": subscription.billing_cycle,
            "billing_day": subscription.billing_day,
            "start_date": subscription.start_date.isoformat(),
            "end_date": subscription.end_date.isoformat(),
            "status": subscription.status,
            "description": subscription.description,
        },
        "payments": [
            {
                "id": p.id,
                "amount": float(p.amount),
                "date": p.date.isoformat(),
                "is_paid": p.is_paid,
            }
            for p in payments
        ],
    })


@csrf_exempt
def subscriptions_create(request):
    """POST: Create new subscription"""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        data = json.loads(request.body)

        subscription = Subscription.objects.create(
            user=request.user,
            name=data.get("name"),
            amount=data.get("amount"),
            category=data.get("category"),
            billing_cycle=data.get("billing_cycle"),
            billing_day=data.get("billing_day"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date", None),
            status=data.get("status", "active"),
            description=data.get("description", ""),
        )

        from .services.subscription_service import generate_payments_for_subscription
        from django.utils import timezone

        try:
            generate_payments_for_subscription(subscription, timezone.now().date())
            print("Payments generated")
        except Exception as e:
            print("Payment generation failed (non-critical):", e)

        return JsonResponse({
            "meesage": "Subscription created",
            "subscription": {
                "id": subscription.id,
                "name": subscription.name,
            }
        }, status=201)
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
    
@csrf_exempt
def subscription_update(request, subscription_id):
    """PATCH: Update subscription"""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    if request.method != "PATCH":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        subscription = Subscription.objects.get(id=subscription_id, user=request.user)
    except Subscription.DoesNotExist:
        return JsonResponse({"error": "Subscription not found"}, status=404)
    
    try:
        from django.utils import timezone

        data = json.loads(request.body)

        # Update allowed fields
        if "name" in data:
            subscription.name = data["name"]
        if "amount" in data:
            subscription.amount = data["amount"]
        if "category" in data:
            subscription.category = data["category"]
        if "billing_cycle" in data:
            subscription.billing_cycle = data["blling_cycle"]
        if "billing_day" in data:
            subscription.billing_day = data["billing_day"]
        if "status" in data:
            subscription.status = data["status"]
            # If cancelling, set end_date
            if data["status"] == "cancelled" and not subscription.end_date:
                subscription.end_date = timezone.now().date()
        if "description" in data:
            subscription.description = data["description"]
        if "end_date" in data:
            subscription.end_date = data["end_date"] or None
        
        subscription.save()

        return JsonResponse({
            "message": "Subscription updated",
            "subscription": {
                "id": subscription.id,
                "name": subscription.name,
                "status": subscription.status,
            }
        })
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
    
@csrf_exempt
def subscription_delete(request, subscription_id):
    """DELETE: Delete subscription and its payments"""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    if request.method != "DELETE":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        subscription = Subscription.objects.get(id=subscription_id, user=request.user)
        subscription.delete()

        return JsonResponse({"message": "Subscription deleted"})
    except Subscription.DoesNotExist:
        return JsonResponse({"error": "Subscription not found"}, status=404)
    

@csrf_exempt
def subscription_update_status(request, subscription_id):
    """PATCH: Quick status update (active/paused/cancelled)"""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    if request.method != "PATCH":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        subscription = Subscription.objects.get(id=subscription_id, user=request.user)

    except Subscription.DoesNotExist:
        return JsonResponse({"error": "Subscription not found"}, status=404)
    
    try:
        data = json.loads(request.body)
        new_status = data.get("status")

        if new_status not in ["active", "paused", "cancelled"]:
            return JsonResponse({"error": "Invalid status"}, status=400)
        
        subscription.status = new_status

        from django.utils import timezone
        # Set end_date when cancelling
        if new_status == "cancelled" and not subscription.end_date:
            subscription.end_date = timezone.now().date()

        # Clear end_date when reactivating
        if new_status == "active":
            subscription.end_date = None
        
        subscription.save()

        return JsonResponse({
            "message": f"Subscription {new_status}",
            "subscription": {
                "id": subscription.id,
                "status": subscription.status,
                "end_date": subscription.end_date.isoformat() if subscription.end_date else None,
            }
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
    
@csrf_exempt
def payment_toggle_paid(request, payment_id):
    """PATCH: Toggle payment is_paid status"""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    if request.method != "PATCH":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        payment = SubscriptionPayment.objects.get(
            id=payment_id,
            subscription__user=request.user
        )
    except SubscriptionPayment.DoesNotExist:
        return JsonResponse({"error": "Payment not found"}, status=404)
    
    from django.utils import timezone
    
    payment.is_paid = not payment.is_paid
    payment.paid_date = timezone.now().date() if payment.is_paid else None
    payment.save()

    return JsonResponse({
        "message": "Payment updated",
        "payment": {
            "id": payment.id,
            "is_paid": payment.is_paid,
            "paid_date": payment.paid_date.isoformat() if payment.paid_date else None,
        }
    })
    

def add_transaction(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )
    
    try: 
        if request.method == "POST":
            Transaction.objects.create(
                user=request.user,
                description=request.POST.get("description"),
                amount=request.POST.get("amount"),
                category=request.POST.get("category")
            )
            return JsonResponse({"status": "Transaction added successfully"})
    except Exception as e:
        logger.error(f"Error adding transaction: {e}")
        return JsonResponse({"error": "Failed to add transaction"}, status=500)


# ====================== INCOME VIEWS ======================#
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
            print(incomes)
            # Get summary calculations (includes transactions + subscriptions)
            summary = compute_income_summary(request.user)
            by_source = compute_income_by_source(request.user)

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
    # elif request.method == "POST":
    #     try:
    #         data = json.loads(request.body)
    #         amount = data.get("amount")
    #         source = data.get("source")
    #         date_received = data.get("date_received")
    #         period_start = data.get("period_start")
    #         period_end = data.get("period_end")

    #         Income.objects.create(
    #             user=request.user,
    #             amount=amount,
    #             source=source,
    #             date_received=date_received,
    #             period_start=period_start,
    #             period_end=period_end
    #         )
    #         return JsonResponse({"status": "Income added successfully"}, status=201)
    #     except Exception as e:
    #         logger.error(f"Error adding income: {e}")
    #         return JsonResponse({"error": "Failed to add income"}, status=500)
    # elif request.method == "DELETE":
    #     try:
    #         data = json.loads(request.body)
    #         ids = data.get("ids", [])
    #         Income.objects.filter(id__in=ids, user=request.user).delete()
    #         return JsonResponse({"status": "deleted"})
    #     except Exception as e:
    #         return JsonResponse({"error": str(e)}, status=400)
    
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

