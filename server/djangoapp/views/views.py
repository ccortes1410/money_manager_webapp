from django.forms import model_to_dict
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import Sum, Q
from ..models.models import Transaction, Budget, Subscription, SubscriptionPayment, Income
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
from ..restapi import get_request
from ..services.budgets import (
    reset_expired_budgets,
    compute_budget_spent,
    get_transactions_for_budget,
    update_budget,
    get_subscriptions_for_budget
)
from ..services.date_filter import (
    filter_queryset_by_period,
    get_period_label,
    get_period_display_dates
)
from ..services.transactions import get_transactions_chart_data
from ..services.category_service import compute_spending_by_category
from ..services.subscription_service import (
    get_subscriptions_for_period,
    compute_subscription_summary,
    compute_subscription_total
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

            from ..services.subscription_service import generate_subscription_payments
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
