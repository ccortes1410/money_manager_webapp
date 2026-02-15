from ..models.models import Subscription, SubscriptionPayment
from django.db.models import Sum
from django.http import JsonResponse
import json
import logging
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..services.subscription_service import (
    get_subscriptions_for_period,

)

logger = logging.getLogger(__name__)



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
                
                summary = get_subscriptions_for_period(user=request.user, period=sub.billing_cycle)
                # print("Subscription summary", summary)
                # print("Subscriptions data, payments:", data[0]["payments"][0]["amount"])
            return JsonResponse({
                "subscriptions": data,
                "summary": summary,
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

        from ..services.subscription_service import generate_payments_for_subscription
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
            subscription.billing_cycle = data["billing_cycle"]
        if "billing_day" in data:
            subscription.billing_day = data["billing_day"]
        if "status" in data:
            subscription.status = data["status"]
            # If cancelling, set end_date
            if data["status"] == "cancelled" and not subscription.end_date:
                subscription.end_date = timezone.now().date()
        if "description" in data:
            subscription.description = data["description"]
        if "start_date" in data:
            subscription.start_date = data["start_date"]
        if "end_date" in data:
            subscription.end_date = data["end_date"] or None
        print(data)
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