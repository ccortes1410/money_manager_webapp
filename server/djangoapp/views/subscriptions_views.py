import json
import logging
from decimal import Decimal

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..restapi import get_request, post_request, patch_request, delete_request
from ..services.api_adapters import subscription_from_row, subscription_payment_from_row
from ..services.date_filter import get_date_bounds

logger = logging.getLogger(__name__)

def _iso_date(dt):
    """Normalize a datetime or date into a plain YYYY-MM-DD string."""
    return dt.date().isoformat() if hasattr(dt, "date") else dt.isoformat()

def get_subscriptions_data(user, period):
    """Get subscription summary for dashboard."""
    start, end = get_date_bounds(period)

    subscription_params = {"user_id": user.id, "status": "active"}
    payment_params = {"user_id": user.id}

    if start and end:
        subscription_params["start_date__lte"]= _iso_date(end) # Started before or during period
        subscription_params["end_date__gte"] = _iso_date(start) # Ends after or during period (or NULL)
        payment_params["due_date__gte"] = _iso_date(start)
        payment_params["due_date__lte"] = _iso_date(end)

    # Get active subscriptions for the period
    subscriptions = get_request("subscriptions/", **subscription_params) or []
    # Get payments for the period
    payments = get_request("subscription-payments/", **payment_params) or []

    # Calculate totals
    subscription_total = sum((Decimal(str(s["amount"])) for s in subscriptions), Decimal('0'))
    payment_total = sum((Decimal(str(s["amount"])) for p in payments), Decimal('0'))

    return {
        "subscription_total": float(subscription_total),
        "payment_total": float(payment_total),
        "subscription_count": len(subscriptions),
        "payment_count": len(payments),
    }


def get_subscriptions(request):
    """Get all subscriptions for user."""
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )
    
    if request.method != "GET":
        return JsonResponse(
            {"error": "Method not allowed"}, status=405
        )

    try:
        rows = get_request("subscriptions/", user_id=request.user.id) or []
        subscriptions = [subscription_from_row(r) for r in rows]
        subscriptions.sort(key=lambda s: s.created_at, reverse=True)

        data = []
        for sub in subscriptions:
            # Get recent payments for this subscription
            payment_rows = get_request("subscription-payments/", subscription_id=sub.id) or []
            payments = [subscription_payment_from_row(p) for p in payment_rows]
            payments.sort(key=lambda p: p.paid_date or p.due_date, reverse=True)

            recent_payments = payments[:5] # Limit to 5 most recent

            # Calculate total paid
            total_paid = sum((p.amount for p in payments if p.is_paid), Decimal('0'))

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
                        "paid_date": p.paid_date.isoformat() if p.paid_date else None,
                        "is_paid": p.is_paid,
                    }
                    for p in recent_payments
                ],
                "total_paid": float(total_paid),
                "payment_count": len(payments),
            })
            
            # Get summary data
            summary = get_subscriptions_data(request.user, "monthly")

            return JsonResponse({
                "subscriptions": data,
                "summary": summary,
                "user": {
                    "id": request.user.id,
                    "username": request.user.username,
                    "is_authenticated": request.user.is_authenticated
                }
            })
                          
    except Exception as e:
        logger.error(f"Error fetching subscriptions: {e}")
        return JsonResponse({"error": "Failed to fetch subscriptions"}, status=500)

@csrf_exempt
def subscription_create(request):
    """Create new subscription."""
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )

    if request.method != "POST":
        return JsonResponse(
            {"error": "Method not allowed"}, status=405
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON"}, status=400
        )

    required_fields = ["name", "amount", "category", "billing_cycle", "billing_day", "start_date"]
    for field in required_fields:
        if field not in data:
            return JsonResponse(
                {"error": f"Missing field: {field}"}, status=400
            )

    row = post_request("subscriptions/", {
        "user_id": request.user.id,
        "name": data["name"],
        "amount": str(data["amount"]),
        "category": data["category"],
        "billing_cycle": data["billing_cycle"],
        "billing_day": int(data["billing_day"]),
        "start_date": data["start_date"],
        "end_date": data.get("end_date"),
        "status": data.get("status", "active"),
        "description": data.get("description", ""),
        "created_at": data.get("creted_at", None)
    })

    if not row:
        return JsonResponse(
            {"error": "Failed to create subscription"}, status=500
        )

    subscription = subscription_from_row(row)

    # Generate initial payments (non-critical, so we don't fail if this has issues)

    try:
        # In a real implementation, we might cal a payments generation endpoint
        # For now, we'll skip this as it's marked non-critical in the original code
        pass
    except Exception as e:
        logger.warning(f"Payment generation failed (non-critical): {e}")

    return JsonResponse({
        "message": "Susbcription created",
        "subscription": {
            "id": subscription.id,
            "name": subscription.name,
            "amount": float(subscription.amount),
            "start_date": subscription.start_date,
            "end_date": subscription.end_date,
            "billing_cycle": subscription.billing_cycle,
            "billing_day": subscription.billing_day,
            "status": subscription.status,
        }
    }, status=201)


@csrf_exempt
def subscriptions_detail(request, subscription_id):
    """GET: Single subscription with all payments"""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    if request.method != "GET":
        return JsonResponse(
            {"error": "Method not allowed"}, status=405
        )

    try:
        # Verify subscription belongs to user
        row = get_request(f"subscriptions/{subscription_id}")
        if not row or row["user_id"] != request.user.id:
            return JsonResponse(
                {"error": "Subscription not found"}, status=404
            )
        
        subscription = subscription_from_row(row)

        # Get all payments for this subscription
        payment_rows = get_request(
            "subscription-payments/",
            subscription_id=subscription.id
        ) or []
        payments = [subscription_payment_from_row(p) for p in payment_rows]
        payments.sort(key=lambda p: p.paid_date or p.due_date, reverse=True)

        return JsonResponse({
            "subscription": {
                "id": subscription.id,
                "name": subscription.name,
                "amount": float(subscription.amount),
                "category": subscription.category,
                "billing_cycle": subscription.billing_cycle,
                "billing_day": subscription.billing_day,
                "start_date": subscription.start_date.isoformat() if subscription.start_date else None,
                "end_date": subscription.end_date.isoformat() if subscription.end_date else None,
                "status": subscription.status,
                "description": subscription.description,
            },
            "payments": [
                {
                    "id": p.id,
                    "amount": float(p.amount),
                    "due_date": p.due_date if p.due_date else None,
                    "paid_date": p.paid_date if p.paid_date else None,
                    "is_paid": p.is_paid,
                }
                for p in payments
            ]
        })
    except Exception as e:
        logger.error(f"Error fetching subscription detail: {e}")
        return JsonResponse(
            {"error": "Failed to fetch subscription details"}, status=500
        )


@csrf_exempt
def subscriptions_create(request):
    """POST: Create new subscription. Kept for backward compatibility."""
    return subscription_create(request)
    
@csrf_exempt
def subscription_update(request, subscription_id):
    """PATCH: Update subscription"""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    if request.method != "PATCH":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        # Verify subscription belongs to user
        row = get_request(f"subscriptions/{subscription_id}")
        if not row or row["user_id"] != request.user.id:
            return JsonResponse(
                {"error": "Subscription not found"}, status=404
            )

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON"}, status=400
            )

        # Prepare update payload
        allowed_fields = [
            "name", "amount", "category", "billing_cycle", "billing_day",
            "status", "description", "start_date", "end_date"
        ]
        payload = {}
        for field in allowed_fields:
            if field in data:
                # Convert amount to string for API compatibility
                if field == "amount":
                    payload[field] = str(data[field])
                elif field == "billing_day":
                    payload[field] = int(data[field])
                else:
                    payload[field] = data[field]

        if not payload:
            return JsonResponse(
                {"error": "No valid fields to update"}, status=400
            )

        updated = patch_request(f"subscriptions/{subscription_id}", payload)
        if not updated:
            return JsonResponse(
                {"error": "Failed to update subscription"}, status=500
            )

        subscription = subscription_from_row(updated)

        return JsonResponse({
            "message": "Subscription updated",
            "subscription": {
                "id": subscription.id,
                "name": subscription.name,
                "status": subscription.status,
            }
        })
    
    except Exception as e:
        logger.error(f"Error updating subscription: {e}")
        return JsonResponse({"error": str(e)}, status=400)

    
@csrf_exempt
def subscription_delete(request, subscription_id):
    """DELETE: Delete subscription and its payments"""
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )

    if request.method != "DELETE":
        return JsonResponse(
            {"error": "Method Not Allowed"}, status=405
        )
    
    try:
        # Verify subscription belongs to user
        row = get_request(f"subscriptions/{subscription_id}")
        if not row or row["user_id"] != request.user.id:
            return JsonResponse(
                {"error": "Subscription not found"}, status=404
            )

        result = delete_request(f"subscriptions/{subscription_id}")
        if result is None:
            return JsonResponse(
                {"error": "Failed to delete subscription"}, status=500
            )

        return JsonResponse({"message": "Subscription deleted"})
    except Exception as e:
        logger.error(f"Error deleting subscription: {e}")
        return JsonResponse(
            {"error": str(e)}, status=401
        )
    

@csrf_exempt
def subscription_update_status(request, subscription_id):
    """PATCH: Quick status update (active/paused/cancelled)"""
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )

    if request.method != "PATCH":
        return JsonResponse(
            {"error": "Method Not Allowed"}, status=405
        )
    
    try:
        # Verify subscription belongs to user
        row = get_request(f"subscriptions/{subscription_id}")
        if not row or row["user_id"] != request.user.id:
            return JsonResponse(
                {"error": "Subscription not found"}, status=404
            )

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON"}, status=400
            )

        new_status = data.get("status")

        if new_status not in ["active", "paused", "cancelled"]:
            return JsonResponse({"error": "Invalid status"}, status=400)
        
        payload = {"status": new_status}

        # Handle end_date logic
        if new_status == "cancelled":
            # Only set end_date if not already set
            if not row.get("end_date"):
                from django.utils import timezone
                payload["end_date"] = timezone.now().date().isoformat()
            elif new_status == "active":
                # Clear end_date when reactivating
                payload["end_date"] = None

        updated = patch_request(f"subscriptions/{subscription_id}", payload)
        if not updated:
            return JsonResponse(
                {"error": "Failed to update subscription status"}, status=500
            )

        subscription = subscription_from_row(updated)

        return JsonResponse({
            "message": f"Subscription {new_status}",
            "subscription": {
                "id": subscription.id,
                "status": subscription.status,
                "end_date": subscription.end_date.isoformat() if subscription.end_date else None,
            }
        })
    except Exception as e:
        logger.error(f"ERror updating subscription status: {e}")
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def payment_toggle_paid(request, payment_id):
    """PATCH: Toggle payment is_paid status"""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    if request.method != "PATCH":
        return JsonResponse({"error": "Method Not Allowed"}, status=405)
    
    try:
        # Verify payment belongs to user via subscription
        # First get the payment to check its subscription
        payment_row = get_request(f"subscription-payments/{payment_id}")
        if not payment_row:
            return JsonResponse(
                {"error": "Payment not found"}, status=404
            )

        # Then check if the subscription belongs to user
        subscription_row = get_request(f"subscriptions/{payment_row['subscription_id']}")
        if not subscription_row or subscription_row["user_id"] != request.user.id:
            return JsonResponse(
                {"error": "Payment not found"}, status=404
            )

        # Toggle the payment status
        current_status = payment_row.get("is_paid", False)
        payload = {"is_paid": not current_status}

        # Set paid_date when marking as paid, clear when marking as unpaid
        if not current_status: # Was unpaid, now marking as paid
            from django.utils import timezone
            payload["paid_date"] = timezone.now().date().isoformat()
        else: # Was paid, now marking unpaid
            payload["paid_date"] = None

        updated = patch_request(f"subscription-payments/{payment_id}", payload)
        if not updated:
            return JsonResponse(
                {"error": "Failed to update payment"}, status=500
            )

        payment = subscription_payment_from_row(updated)

        return JsonResponse({
            "message": "Payment updated",
            "payment": {
                "id": payment.id,
                "is_paid": payment.is_paid,
                "paid_date": payment.paid_date.isoformat() if payment.paid_date else None,
            }
        })

    except Exception as e:
        logger.error(f"Error updating payment: {e}")
        return JsonResponse(
            {"error": str(e)}, status=400
        )
