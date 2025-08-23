from django.shortcuts import render
from django.http import HttpResponseRedirect
from .models import Transaction
from django.contrib.auth.models import User
from django.http import JsonResponse
import json
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.decorators import csrf_exempt
from django.contrib.auth import authenticate, login, logout
import logging

logger = logging.getLogger(__name__)


def register_user(request):
    context = {}
    if request.method == "GET":
        return render(request, "moneymanager/user_registration_bootstrap.html", context)
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

def login_user(request):

    data = json.loads(request.body)
