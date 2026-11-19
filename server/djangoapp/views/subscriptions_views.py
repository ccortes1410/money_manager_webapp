import json
import logging
from decimal import Decimal

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..restapi import get_request, post_request, patch_request, delete_request
from ..services.api_adapters import subscription_from_row, subscription_payment_from_row
from ..services.date_filter import get_date_bounds
from ..services.subscription_service import generate_subscription_payments as generate_subscription_payments_service

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
        subscription_params["start_date__lte"] = _iso_date(end)  # Started before or during period
        subscription_params["end_date__gte"] = _iso_date(start)  # Ends after or during period (or NULL)
        payment_params["due_date__gte"] = _iso_date(start)
        payment_params["due_date__lte"] = _iso_date(end)

    # Get active subscriptions for the period
    subscriptions = get_request("subscriptions/", **subscription_params) or []
    # Get paid payments for the period
    payments = [
        p for p in (get_request("subscription-payments/", **payment_params) or [])
        if p.get("is_paid", True)
    ]

    # Calculate totals
    subscription_total = sum((Decimal(str(s["amount"])) for s in subscriptions), Decimal('0'))
    payment_total = sum((Decimal(str(p["amount"])) for p in payments), Decimal('0'))

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
        try:
            generate_subscription_payments_service(request.user.id)
        except Exception as gen_err:
            logger.exception(f"Payment generation failed in get_subscriptions: {gen_err}")

        params = {'user_id': request.user.id}
        rows = get_request("subscriptions/", **params) or []
        subscriptions = [subscription_from_row(r) for r in rows]
        subscriptions.sort(key=lambda s: s.created_at, reverse=True)

        data = []
        for sub in subscriptions:
            # Get recent payments for this subscription
            payment_params = {'subscription_id': sub.id}
            payment_rows = get_request("subscription-payments/", **payment_params) or []
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
                        "date": (p.due_date or p.paid_date).isoformat() if (p.due_date or p.paid_date) else None,
                        "due_date": p.due_date.isoformat() if p.due_date else None,
                        "paid_date": p.paid_date.isoformat() if p.paid_date else None,
                        "is_paid": p.is_paid,
                    }
                    for p in recent_payments
                ],
                "total_paid": float(total_paid),
                "payment_count": len(payments),
            })

        # Get summary data after collecting every subscription.
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

def get_subscription_payments(request, subscription_id):
    """Get payments for a specific subscription."""
    if not request.user.is_authenticated:
        return JsonResponse(
            {'error': 'Unauthorized'}, status=401
        )

    if request.method != "GET":
        return JsonResponse(
            {'error': 'Method not allowed'}, status=405
        )

    try:
        # First verify that the subscription belongs to the user
        subscription_row = get_request(f"subscriptions/{subscription_id}")
        if not subscription_row or subscription_row["user_id"] != request.user.id:
            return JsonResponse(
                {'error': 'Subscription not found'}, status=404
            )

        # Get subscription payments for this subscription
        payment_params = {'subscription_id': subscription_id}
        rows = get_request("subscription-payments/", **payment_params) or []
        subscription_payments = [subscription_payment_from_row(row) for row in rows]
        subscription_payments.sort(key=lambda p: p.paid_date or p.due_date, reverse=True)

        total_paid = sum((p.amount for p in subscription_payments if p.is_paid), Decimal('0'))

        data = []
        for p in subscription_payments:
            data.append({
                'id': p.id,
                'subscription_id': p.subscription_id,
                'amount': float(p.amount),
                'due_date': p.due_date.isoformat() if p.due_date else None,
                'paid_date': p.paid_date.isoformat() if p.paid_date else None,
                'is_paid': p.is_paid,
            })

        # Return the list of payments
        return JsonResponse({
            'payments': data,
            'count': len(data),
            'total_paid': float(total_paid)
        })
    except Exception as e:
        logger.error(f"Error fetching payments for subscription {subscription_id}: {e}")
        return JsonResponse({'error': 'Failed to fetch subscription payments'}, status=500)
    
@csrf_exempt
def get_user_subscription_payments(request):
    """Get subscription payments for the current user with optional filtering."""
    if not request.user.is_authenticated:
        return JsonResponse(
            {'error': 'Unauthorized'}, status=401
        )

    if request.method != "GET":
        return JsonResponse(
            {'error': 'Method not allowed'}, status=405
        )

    try:
        # Build query parameters from request.GET
        params = {'user_id': request.user.id}

        # Add any additional filter parameters from the request
        for key, value in request.GET.items():
            if key not in ['user_id']:  # Don't override user_id from request
                params[key] = value

        # Get subscription payments from the API
        try:
            rows = get_request("subscription-payments/", **params)
        except Exception as e:
            logger.error(f"Error calling subscription-payments API: {e}")
            rows = None

        if rows is None:
            rows = []

        subscription_payments = [subscription_payment_from_row(row) for row in rows]
        subscription_payments.sort(key=lambda p: p.paid_date or p.due_date, reverse=True)

        total_paid = sum((p.amount for p in subscription_payments if p.is_paid), Decimal('0'))

        data = []
        for p in subscription_payments:
            data.append({
                'id': p.id,
                'subscription_id': p.subscription_id,
                'amount': float(p.amount),
                'due_date': p.due_date.isoformat() if p.due_date else None,
                'paid_date': p.paid_date.isoformat() if p.paid_date else None,
                'is_paid': p.is_paid,
            })

        # Return the list of payments
        return JsonResponse({
            'payments': data,
            'count': len(data),
            'total_paid': float(total_paid)
        })
    except Exception as e:
        logger.error(f"Error fetching user subscription payments: {e}")
        return JsonResponse({'error': 'Failed to fetch user subscription payments'}, status=500)


@csrf_exempt
def generate_subscription_payments(request):
    """Generate subscription payments for the current user by calling the Node.js backend API."""
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )

    if request.method != "POST":
        return JsonResponse(
            {"error": "Method not allowed"}, status=405
        )

    try:
        # Prepare data for the API request
        data = {
            "user_id": request.user.id
        }

        # Call the Node.js backend API to generate subscription payments
        # Using the endpoint name from the subscription_service.py file
        response = post_request("subscription-payments/generate-for-user", data)

        if response is not None:
            # Successfully called the API
            return JsonResponse({
                "message": "Subscription payments generated",
                "created_count": response.get("created_count", 0)
            })
        else:
            # API call failed, fallback to internal method if needed
            logger.warning(f"Failed to call Node.js generate endpoint for user {request.user.id}, falling back to internal method")
            # Try the internal service function as fallback
            created_count = generate_subscription_payments_service(request.user.id)
            return JsonResponse({
                "message": "Subscription payments generated via internal method",
                "created_count": created_count
            })
    except Exception as e:
        logger.error(f"Error generating subscription payments: {e}")
        return JsonResponse({"error": "Failed to generate subscription payments"}, status=500)


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

    # Log received data for debugging
    logger.debug(f"Received subscription creation data: {data}")

    required_fields = ["name", "amount", "category", "billing_cycle", "billing_day", "start_date"]
    for field in required_fields:
        if field not in data:
            return JsonResponse(
                {"error": f"Missing field: {field}"}, status=400
            )

    # Validate data types and values
    try:
        amount_val = float(data["amount"])
        if amount_val < 0:
            return JsonResponse(
                {"error": "Amount must be non-negative"}, status=400
            )

        billing_day_val = int(data["billing_day"])
        if billing_day_val < 1:
            return JsonResponse(
                {"error": "Billing day must be positive"}, status=400
            )
    except (ValueError, TypeError) as e:
        return JsonResponse(
            {"error": f"Invalid data type: {str(e)}"}, status=400
        )

    # Prepare payload for Node.js backend
    from datetime import datetime
    now = datetime.now().isoformat()
    payload = {
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
        "created_at": now,
        "updated_at": now
    }

    # Log payload being sent
    logger.debug(f"Sending payload to Node.js backend: {payload}")

    row = post_request("subscriptions/", payload)

    # Debug: Log exactly what we got back from the backend
    logger.debug(f"Raw response from Node.js backend: {row}")

    if row is None:
        logger.error("Node.js backend returned None response")
        return JsonResponse(
            {"error": "Failed to create subscription - no response from backend"}, status=500
        )

    if isinstance(row, dict) and "error" in row:
        logger.error(f"Node.js backend returned error: {row['error']}")
        return JsonResponse(
            {"error": f"Backend error: {row['error']}"}, status=400
        )

    subscription = subscription_from_row(row)

    try:
        generate_subscription_payments_service(request.user.id)
    except Exception as e:
        logger.warning(f"Payment generation failed (non-critical): {e}")

    return JsonResponse({
        "message": "Subscription created",
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
def subscription_detail(request, subscription_id):
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
        # Convert Django-style lookups to single underscore for Node.js API
        payment_params = {'subscription_id': subscription.id}
        payment_params = {k.replace('__', '_'): v for k, v in payment_params.items()}
        payment_rows = get_request(
            "subscription-payments/",
            **payment_params
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

        try:
            generate_subscription_payments_service(request.user.id)
        except Exception as e:
            logger.warning(f"Payment reconciliation after update failed (non-critical): {e}")

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

        try:
            generate_subscription_payments_service(request.user.id)
        except Exception as e:
            logger.warning(f"Payment reconciliation after update failed (non-critical): {e}")

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
        current_status = bool(payment_row.get("is_paid", False))
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


@csrf_exempt
def subscription_payment_create(request):
    """Create a new subscription payment."""
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

    # Validate required fields
    required_fields = ["subscription_id", "due_date", "amount"]
    for field in required_fields:
        if field not in data:
            return JsonResponse(
                {"error": f"Missing field: {field}"}, status=400
            )

    # Prepare payment data
    from datetime import datetime
    payment_data = {
        "user_id": request.user.id,
        "subscription_id": data["subscription_id"],
        "due_date": data["due_date"],
        "amount": str(data["amount"]),  # Convert to string for API compatibility
        "is_paid": data.get("is_paid", False),
        "created_at": datetime.now().isoformat(),
    }

    # If marking as paid, set paid_date to today
    if payment_data["is_paid"] and not data.get("paid_date"):
        from django.utils import timezone
        payment_data["paid_date"] = timezone.now().date().isoformat()
    elif "paid_date" in data:
        payment_data["paid_date"] = data["paid_date"]

    # Create via API
    row = post_request("subscription-payments/", payment_data)

    if not row or "error" in row:
        return JsonResponse(
            {"error": "Failed to create subscription payment"}, status=500
        )

    payment = subscription_payment_from_row(row)

    return JsonResponse({
        "message": "Subscription payment created",
        "payment": {
            "id": payment.id,
            "subscription_id": payment.subscription_id,
            "amount": float(payment.amount),
            "due_date": payment.due_date.isoformat() if payment.due_date else None,
            "is_paid": payment.is_paid,
            "paid_date": payment.paid_date.isoformat() if payment.paid_date else None,
        }
    }, status=201)


@csrf_exempt
def subscription_payment_detail(request, payment_id):
    """Get a single subscription payment."""
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )

    if request.method != "GET":
        return JsonResponse(
            {"error": "Method not allowed"}, status=405
        )

    try:
        # Get the payment to verify ownership via subscription
        payment_row = get_request(f"subscription-payments/{payment_id}")
        if not payment_row:
            return JsonResponse(
                {"error": "Payment not found"}, status=404
            )

        # Check if the subscription belongs to the user
        subscription_row = get_request(f"subscriptions/{payment_row['subscription_id']}")
        if not subscription_row or subscription_row["user_id"] != request.user.id:
            return JsonResponse(
                {"error": "Payment not found"}, status=404
            )

        payment = subscription_payment_from_row(payment_row)

        return JsonResponse({
            "payment": {
                "id": payment.id,
                "subscription_id": payment.subscription_id,
                "amount": float(payment.amount),
                "due_date": payment.due_date.isoformat() if payment.due_date else None,
                "is_paid": payment.is_paid,
                "paid_date": payment.paid_date.isoformat() if payment.paid_date else None,
            }
        })
    except Exception as e:
        logger.error(f"Error fetching payment {payment_id}: {e}")
        return JsonResponse({"error": "Failed to fetch payment"}, status=500)


@csrf_exempt
def subscription_payment_update(request, payment_id):
    """Update a subscription payment."""
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )

    if request.method != "PATCH":
        return JsonResponse(
            {"error": "Method not allowed"}, status=405
        )

    try:
        # First verify the payment belongs to the user via subscription
        payment_row = get_request(f"subscription-payments/{payment_id}")
        if not payment_row:
            return JsonResponse(
                {"error": "Payment not found"}, status=404
            )

        subscription_row = get_request(f"subscriptions/{payment_row['subscription_id']}")
        if not subscription_row or subscription_row["user_id"] != request.user.id:
            return JsonResponse(
                {"error": "Payment not found"}, status=404
            )

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON"}, status=400
            )

        # Prepare update payload
        allowed_fields = ["due_date", "amount", "is_paid", "paid_date"]
        payload = {}
        for field in allowed_fields:
            if field in data:
                if field == "amount":
                    payload[field] = str(data[field])
                else:
                    payload[field] = data[field]

        if not payload:
            return JsonResponse(
                {"error": "No valid fields to update"}, status=400
            )

        # Handle is_paid and paid_date logic
        if "is_paid" in payload:
            if payload["is_paid"] and not payload.get("paid_date"):
                from django.utils import timezone
                payload["paid_date"] = timezone.now().date().isoformat()
            elif not payload["is_paid"]:
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
                "subscription_id": payment.subscription_id,
                "amount": float(payment.amount),
                "due_date": payment.due_date.isoformat() if payment.due_date else None,
                "is_paid": payment.is_paid,
                "paid_date": payment.paid_date.isoformat() if payment.paid_date else None,
            }
        })
    except Exception as e:
        logger.error(f"Error updating payment {payment_id}: {e}")
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def subscription_payment_delete(request, payment_id):
    """Delete a subscription payment."""
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )

    if request.method != "DELETE":
        return JsonResponse(
            {"error": "Method not allowed"}, status=405
        )

    try:
        # First verify the payment belongs to the user via subscription
        payment_row = get_request(f"subscription-payments/{payment_id}")
        if not payment_row:
            return JsonResponse(
                {"error": "Payment not found"}, status=404
            )

        subscription_row = get_request(f"subscriptions/{payment_row['subscription_id']}")
        if not subscription_row or subscription_row["user_id"] != request.user.id:
            return JsonResponse(
                {"error": "Payment not found"}, status=404
            )

        result = delete_request(f"subscription-payments/{payment_id}")
        if result is None:
            return JsonResponse(
                {"error": "Failed to delete payment"}, status=500
            )

        return JsonResponse({"message": "Payment deleted"})
    except Exception as e:
        logger.error(f"Error deleting payment {payment_id}: {e}")
        return JsonResponse({"error": str(e)}, status=400)
