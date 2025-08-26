from django.shortcuts import render
from django.http import HttpResponseRedirect
from .models import Transaction
from django.contrib.auth.models import User
from django.http import JsonResponse
import json
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
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
    return JsonResponse(data)

def get_transactions(request):
    try:
        if request.method == "GET":
            transactions = Transaction.objects.filter(user=request.user)
            data = {"transactions": list(transactions.values())}
            return JsonResponse(data)
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        return JsonResponse({"error": "Failed to fetch transactions"}, status=500)

def add_transaction(request):
    try: 
        if request.method == "POST":
            Transaction.objects.create(
                user = request.user,
                description = request.POST.get("description"),
                amount = request.POST.get("amount")
            )
            return JsonResponse({"status": "Transaction added successfully"})
    except Exception as e:
        logger.error(f"Error adding transaction: {e}")
        return JsonResponse({"error": "Failed to add transaction"}, status=500)