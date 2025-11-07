from django.forms import model_to_dict
from django.shortcuts import render
from django.http import HttpResponseRedirect
from .models import Transaction, Budget
from django.contrib.auth.models import User
from django.http import JsonResponse
import json
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .restapi import get_request
import logging

logger = logging.getLogger(__name__)


def register_user(request):
    context = {}
    if request.method == "GET":
        return render(request, "money_manager/user_registration_bootstrap.html", context)
    elif request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")

        user = User(username=username, email=email)
        user.set_password(password)
        user.save()
        user_exist = False
        
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name, email=email, password=password)
        logger.info(f"User registered: {username}")
        return HttpResponseRedirect(reverse("login"))

    return render(request, "register.html")

def login_request(request):
    
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']

    user = authenticate(username=username, password=password)
    data = {"userName": username}
    if user is not None:

        login(request, user)
        data = {"userName": username, "status": "Authenticated"}

    return JsonResponse(data)

def logout_request(request):

    logout(request)
    data = {"userName": ""}
    return JsonResponse({"status": "logged_out"})

@login_required
def dashboard(request):
    # print(request.user)
    category = request.GET.get("category")
    print(category)
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


@login_required
def budget_list(request, budget_id=None):
    if request.method == "GET":
        try:
            budgets = Budget.objects.filter(user=request.user)
            data = list(budgets.values())
            return JsonResponse({
                "budgets": data,
                "user": {
                    "id": request.user.id,
                    "username": request.user.username,
                    "is_authenticated": request.user.is_authenticated
                }
            })  
        except Exception as e:
            logger.error(f"Error fetching budget: {e}")
            return JsonResponse({"error": "Failed to fetch budget"}, status=500)
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            name = data.get("name")
            amount = data.get("amount")
            period = data.get("period")
            Budget.objects.create(
                user=request.user,
                name=name,
                amount=amount,
                period=period
            )
            return JsonResponse({"status": "Budget added successfully"}, status=201)
        except Exception as e:
            logger.error(f"Error adding budget: {e}")
            return JsonResponse({"error": "Failed to add budget"}, status=500)
    elif request.method == "DELETE" and budget_id is not None:
        try:
            Budget.objects.filter(id=budget_id, user=request.user).delete()
            return JsonResponse({"status": "deleted"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


@login_required
def budget_detail(request, budget_id):
    # budget_id = request.GET.get("id")
    try:
        if not budget_id:
            logger.error("No Budget ID provided")
            return JsonResponse({"error": "Budget ID is required"}, status=400)

        logger.info(f"Fetching budget with ID: {budget_id} for user: {request.user.username}")
        budget = Budget.objects.get(id=budget_id, user=request.user)
        logger.info(f"Budget found: {budget}")

        data = model_to_dict(budget)
        logger.debug(f"Budget details: {data}")
        return JsonResponse({
            "budget": data,
            "user": {
                "id": request.user.id,
                "username": request.user.username,
                "is_authenticated": request.user.is_authenticated
            }       
        })
    except Budget.DoesNotExist:
        return JsonResponse({"error": "Budget not found"}, status=404)

# @login_required
# def add_budget(request):
#     try:
#         if request.method == "POST":
#             data = json.loads(request.body)
#             name = data.get("name")
#             amount = data.get("amount")
#             period = data.get("period")
#             Budget.objects.create(
#                 user=request.user,
#                 name=name,
#                 amount=amount,
#                 period=period
#             )
#             return JsonResponse({"status": "Budget added successfully"}, status=201)
#     except Exception as e:
#         logger.error(f"Error adding budget: {e}")
#         return JsonResponse({"error": "Failed to add budget"}, status=500)
    

@login_required
def subscriptions(request):
    try:
        if request.method == "GET":
            return get_request(request, "fetchSubscriptions")
    except Exception as e:
        logger.error(f"Error fetching subscriptions: {e}")
        return JsonResponse({"error": "Failed to fetch subscriptions"}, status=500)
    return render(request, "money_manager/subscriptions.html")
    


@login_required
def add_transaction(request):
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