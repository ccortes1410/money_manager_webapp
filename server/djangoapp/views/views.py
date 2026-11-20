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
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.conf import settings as django_settings
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from ..restapi import get_request
from ..services.budgets_service import (
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
    compute_subscription_summary
    )
from ..services.spending_calculations import compute_subscription_total
from django_ratelimit.decorators import ratelimit

import logging

logger = logging.getLogger(__name__)

# ======================= AUTH VIEWS ======================= #
@csrf_exempt
@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def register_view(request):
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
            login(request, user)
            logger.info(f"User registered: {username}")
            return JsonResponse({"status": True, "id": user.id, "userName": username}, status=201)
        except Exception as e:
            logger.exception(f"Error registering user: {e}")
            return JsonResponse({"error": f"Failed to register user: {e}"}, status=500)

    return render(request, "register.html")

def _serialize_user(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email or "",
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "date_joined": user.date_joined.isoformat() if user.date_joined else None,
        "is_authenticated": True,
    }


@csrf_exempt
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login_request(request):
    
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    
    try:
        res = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)
    
    user = authenticate(
        request,
        username=res.get("username"),
        password=res.get("password"),
    )

    if user is not None:
        login(request, user)
        return JsonResponse(_serialize_user(user))

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
    
    return JsonResponse({"user": _serialize_user(request.user)})

def session_view(request):
    if request.user.is_authenticated:
        return JsonResponse(_serialize_user(request.user))
    return JsonResponse({"is_authenticated": False})


# ======================= PASSWORD RESET ======================= #

@csrf_exempt
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def password_reset_request(request):
    """Send a password reset email with a time-limited token link."""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    email = (data.get("email") or "").strip()
    if not email:
        return JsonResponse({"error": "Email is required"}, status=400)

    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({"error": "Please enter a valid email address"}, status=400)

    generic_msg = "If an account with that email exists, a password reset link has been sent."

    users = User.objects.filter(email__iexact=email, is_active=True)
    if users.exists():
        frontend_base = getattr(django_settings, "FRONTEND_URL", "")
        if not frontend_base:
            origin = request.META.get("HTTP_ORIGIN")
            if origin:
                frontend_base = origin.rstrip("/")
            else:
                frontend_base = request.build_absolute_uri("/").rstrip("/")

        for user in users:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = f"{frontend_base}/reset-password/{uid}/{token}"
            try:
                send_mail(
                    subject="Reset your Money Manager password",
                    message=(
                        f"Hi {user.first_name or user.username},\n\n"
                        f"We received a request to reset your Money Manager password.\n"
                        f"Click the link below to set a new password (valid for 1 hour):\n\n"
                        f"{reset_url}\n\n"
                        f"If you didn't request this, you can safely ignore this email."
                    ),
                    from_email=django_settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception as e:
                logger.exception(f"Failed to send password reset email to user {user.id}: {e}")

    return JsonResponse({"message": generic_msg})


@csrf_exempt
@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def password_reset_confirm(request):
    """Validate uid + token and set a new password."""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    uid = (data.get("uid") or "").strip()
    token = (data.get("token") or "").strip()
    new_password = data.get("new_password") or ""

    if not uid or not token or not new_password:
        return JsonResponse({"error": "Reset token and new password are required"}, status=400)

    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id, is_active=True)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return JsonResponse({"error": "Invalid or expired reset link"}, status=400)

    if not default_token_generator.check_token(user, token):
        return JsonResponse({"error": "Invalid or expired reset link"}, status=400)

    try:
        validate_password(new_password, user)
    except ValidationError as ve:
        return JsonResponse({"error": " ".join(ve.messages)}, status=400)

    user.set_password(new_password)
    user.save()
    return JsonResponse({"message": "Password has been reset successfully."})


# ======================= USER SETTINGS / PROFILE ======================= #

@csrf_exempt
def user_profile(request):
    """GET or PATCH the logged-in user's profile information."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    user = request.user

    if request.method == "GET":
        return JsonResponse({"user": _serialize_user(user)})

    if request.method != "PATCH":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if "first_name" in data:
        user.first_name = (data.get("first_name") or "").strip()[:150]
    if "last_name" in data:
        user.last_name = (data.get("last_name") or "").strip()[:150]
    if "email" in data:
        new_email = (data.get("email") or "").strip()
        if new_email:
            try:
                validate_email(new_email)
            except ValidationError:
                return JsonResponse({"error": "Please enter a valid email address"}, status=400)
            if User.objects.filter(email__iexact=new_email).exclude(pk=user.pk).exists():
                return JsonResponse({"error": "That email address is already in use"}, status=400)
        user.email = new_email

    user.save()
    return JsonResponse({
        "message": "Profile updated",
        "user": _serialize_user(user),
    })


@csrf_exempt
def change_password(request):
    """Change password for the currently logged-in user without logging them out."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    current_password = data.get("current_password") or ""
    new_password = data.get("new_password") or ""

    if not current_password or not new_password:
        return JsonResponse({"error": "Current and new passwords are required"}, status=400)

    user = request.user
    if not user.check_password(current_password):
        return JsonResponse({"error": "Current password is incorrect"}, status=400)

    try:
        validate_password(new_password, user)
    except ValidationError as ve:
        return JsonResponse({"error": " ".join(ve.messages)}, status=400)

    user.set_password(new_password)
    user.save()
    update_session_auth_hash(request, user)
    return JsonResponse({"message": "Password updated successfully"})


@csrf_exempt
def delete_account(request):
    """Permanently delete the logged-in user's account after password verification."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    if request.method != "DELETE":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    password = data.get("password") or ""
    if not password:
        return JsonResponse({"error": "Password is required to delete your account"}, status=400)

    user = request.user
    if not user.check_password(password):
        return JsonResponse({"error": "Incorrect password"}, status=400)

    logout(request)
    user.delete()
    return JsonResponse({"message": "Account deleted"})




