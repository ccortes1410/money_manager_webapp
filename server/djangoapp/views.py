from django.forms import model_to_dict
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from .models import Transaction, Budget, Subscription, Income
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


def dashboard(request):
    # print(request.user)
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )
    
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



def budget_list(request, budget_id=None):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )
    
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
            category = data.get("category")
            amount = data.get("amount")
            period = data.get("period")
            reset_day = data.get("reset_day")
            expires_at = data.get("expires_at")

            Budget.objects.create(
                user=request.user,
                category=category,
                amount=amount,
                period=period,
                reset_day=reset_day,
                expires_at=expires_at
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



def budget_detail(request, budget_id):
    # budget_id = request.GET.get("id")
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )
    
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


def subscriptions(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )
    
    try:
        if request.method == "GET":
            subscriptions = Subscription.objects.filter(user=request.user)
            data = list(subscriptions.values())
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
            description = data.get("description")
            amount = data.get("amount")
            category = data.get("category")
            due_date = data.get("due_date")
            frequency = data.get("frequency")
            is_active = data.get("is_active")

            Subscription.objects.create(
                user=request.user,
                description=description,
                amount=amount,
                category=category,
                due_date=due_date,
                frequency=frequency,
                is_active=is_active,
            )
            return JsonResponse({"status": "Subscription added successfully"}, status=201)   
                  
    except Exception as e:
        logger.error(f"Error fetching subscriptions: {e}")
        return JsonResponse({"error": "Failed to fetch subscriptions"}, status=500)
    return render(request, "money_manager/subscriptions.html")


def delete_subs(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )
    
    data = json.loads(request.body)
    ids = data.get('ids', [])
    subs = Subscription.objects.filter(id__in=ids, user=request.user)
    count = subs.count()

    try:
        if request.method == "DELETE":
            subs.delete()
            return JsonResponse(
                {
                "deleted": ids,
                "message": f"{count} subscriptions deleted succesfully."
                },
                status=200,
            )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


def update_subs(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )
    
    data = json.loads(request.body)
    ids = data.get('ids', [])
    is_active = data.get('is_active')
    subs = Subscription.objects.filter(id__in=ids, user=request.user)
    count = subs.count()

    try:
        if request.method == "PATCH":
            subs.update(is_active=is_active)
            return JsonResponse(
                {
                    "updated": ids,
                    "is_active": is_active,
                    "message": f"{count} subscriptions updated succesfully"
                },
                status=200
            )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
    

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
    

def income_list(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )
    
    if request.method == "GET":
        try:
            incomes = Income.objects.filter(user=request.user)
            data = list(incomes.values())
            return JsonResponse({
                "incomes": data,
                "user": {
                    "id": request.user.id,
                    "username": request.user.username,
                    "is_authenticated": request.user.is_authenticated
                }
            })  
        except Exception as e:
            logger.error(f"Error fetching income: {e}")
            return JsonResponse({"error": "Failed to fetch income"}, status=500)
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            amount = data.get("amount")
            source = data.get("source")
            date_received = data.get("date_received")
            period_start = data.get("period_start")
            period_end = data.get("period_end")

            Income.objects.create(
                user=request.user,
                amount=amount,
                source=source,
                date_received=date_received,
                period_start=period_start,
                period_end=period_end
            )
            return JsonResponse({"status": "Income added successfully"}, status=201)
        except Exception as e:
            logger.error(f"Error adding income: {e}")
            return JsonResponse({"error": "Failed to add income"}, status=500)
    elif request.method == "DELETE":
        try:
            data = json.loads(request.body)
            ids = data.get("ids", [])
            Income.objects.filter(id__in=ids, user=request.user).delete()
            return JsonResponse({"status": "deleted"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)