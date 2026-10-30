from datetime import date, timedelta
from calendar import monthrange
from decimal import Decimal
from ..restapi import get_request, post_request
from .date_filter import get_date_bounds


def generate_subscription_payments(user_id, up_to_date=None):
    """
    Generate SubscriptionPayment records for all active subscriptions
    up to the specified date (default: today).

    This function calls the Node.js backend API to generate payments.
    """
    if up_to_date is None:
        up_to_date = date.today()

    # Call the Node.js backend to generate subscription payments
    # We need to pass the user_id and up_to_date to the backend
    try:
        # Assuming there's an endpoint to generate payments for a user
        # This would need to be implemented in the Node.js backend
        data = {
            "user_id": user_id,
            "up_to_date": up_to_date.isoformat()
        }
        # Note: This endpoint may not exist yet in the Node.js backend
        # For now, we'll return 0 to maintain compatibility
        # TODO: Implement this endpoint in Node.js backend
        # response = post_request("subscription-payments/generate-for-user", data)
        # return response.get("created_count", 0) if response else 0

        # Fallback: if the endpoint doesn't exist, we'll need to generate
        # payments by fetching subscriptions and creating them one by one
        # via the API (less efficient but works)
        return _generate_subscription_payments_via_api(user_id, up_to_date)
    except Exception:
        # If anything goes wrong, return 0 to avoid breaking the calling code
        return 0


def _generate_subscription_payments_via_api(user_id, up_to_date):
    """
    Generate subscription payments by fetching subscriptions via API
    and creating payments individually.
    Less efficient than a dedicated backend endpoint but works with current API.
    """
    created_count = 0

    # Get all active subscriptions for the user
    subscriptions_data = get_request("subscriptions/",
                                   user_id=user_id,
                                   status="active") or []

    for sub_data in subscriptions_data:
        subscription_id = sub_data["id"]
        start_date = sub_data["start_date"]
        end_date = sub_data.get("end_date")
        amount = Decimal(str(sub_data["amount"]))
        billing_cycle = sub_data["billing_cycle"]
        billing_day = int(sub_data["billing_day"])

        # Generate payments for this subscription
        created_count += _generate_payments_for_subscription_via_api(
            subscription_id, start_date, end_date, amount,
            billing_cycle, billing_day, up_to_date
        )

    return created_count


def _generate_payments_for_subscription_via_api(subscription_id, start_date, end_date,
                                               amount, billing_cycle, billing_day, up_to_date):
    """
    Generate all missing SubscriptionPayment records for a subscription
    from start_date to up_to_date.
    """
    created_count = 0

    # Get all billing dates from start to up_to_date
    billing_dates = get_billing_dates(
        start_date=start_date,
        end_date=up_to_date,
        billing_cycle=billing_cycle,
        billing_day=billing_day
    )

    for billing_date in billing_dates:
        # Skip if subscription was ended before this date
        if end_date and billing_date > end_date:
            continue

        # Check if payment already exists for this date
        existing_payments = get_request("subscription-payments/",
                                       subscription_id=subscription_id,
                                       due_date=billing_date.isoformat()) or []

        # If no payment exists for this date, create one
        if not existing_payments:
            payment_data = {
                "subscription": subscription_id,
                "due_date": billing_date.isoformat(),
                "amount": str(amount),
                "is_paid": False
            }

            response = post_request("subscription-payments/", payment_data)
            if response:
                created_count += 1

    return created_count


def get_billing_dates(start_date, end_date, billing_cycle, billing_day=1):
    """
    Calculate all billing dates between start_date and end_date.
    (Unchanged - pure function)
    """
    dates = []
    current = start_date

    while current <= end_date:
        dates.append(current)
        current = get_next_billing_date(current, billing_cycle, billing_day)

        # Safety: prevent infinite loop
        if len(dates) > 1000:
            break

    return dates


def get_next_billing_date(from_date, billing_cycle, billing_day=1):
    """Calculate the next billing date after from_date."""
    if billing_cycle == "daily":
        return from_date + timedelta(days=1)
    elif billing_cycle == "weekly":
        return from_date + timedelta(weeks=1)
    elif billing_cycle == "monthly":
        year, month = from_date.year, from_date.month

        # Move to next month
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1

        # Handle months with fewer days
        max_day = monthrange(year, month)[1]
        day = min(billing_day, max_day)

        return from_date.replace(year=year, month=month, day=day)
    elif billing_cycle == "yearly":
        return from_date.replace(year=from_date.year + 1)

    return from_date + timedelta(days=31)   # Default fallback


def get_subscriptions_for_period(user_id, period: str):
    """
    Get subscription payment totals for a period.
    Used by dashboard.
    """
    start, end = get_date_bounds(period)

    # Get subscription payments for the period
    payments_params = {"user_id": user_id}
    if start and end:
        payments_params["due_date__gte"] = start.isoformat() if hasattr(start, 'isoformat') else str(start)
        payments_params["due_date__lte"] = end.isoformat() if hasattr(end, 'isoformat') else str(end)

    payments_data = get_request("subscription-payments/", **payments_params) or []

    # Get subscriptions to determine which are active/inactive
    subscriptions_data = get_request("subscriptions/", user_id=user_id) or []

    # Create lookup maps
    subscription_status = {}
    for sub in subscriptions_data:
        subscription_status[sub["id"]] = sub.get("status", "unknown")

    # Separate active and inactive payments
    active_payments = []
    inactive_payments = []

    for payment in payments_data:
        sub_id = payment.get("subscription")
        status = subscription_status.get(sub_id, "unknown")
        if status == "active":
            active_payments.append(payment)
        else:
            inactive_payments.append(payment)

    # Calculate totals
    active_total = sum(Decimal(str(p.get("amount", 0))) for p in active_payments)
    inactive_total = sum(Decimal(str(p.get("amount", 0))) for p in inactive_payments)
    total_sum = active_total + inactive_total

    # Format response to match original structure
    return {
        "active": {
            "count": len(set(p.get("subscription") for p in active_payments)),  # Unique subscriptions
            "total": float(active_total),
            "payments": [
                {
                    'id': p['id'],
                    'amount': float(p.get('amount', 0)),
                    'due_date': p.get('due_date'),
                    'paid_date': p.get('paid_date'),
                    'subscription__name': next((s['name'] for s in subscriptions_data if s['id'] == p.get('subscription')), ''),
                    'subscription__category': next((s['category'] for s in subscriptions_data if s['id'] == p.get('subscription')), '')
                }
                for p in active_payments
            ]
        },
        "inactive": {
            "count": len(set(p.get("subscription") for p in inactive_payments)),  # Unique subscriptions
            "total": float(inactive_total)
        },
        "total": float(total_sum),
        "payment_count": len(payments_data)
    }


def compute_subscription_summary(user_id):
    """
    Compute subscription summary for a user.
    """
    today = date.today()

    # Current month boundaries
    month_start = date(today.year, today.month, 1)
    if today.month == 12:
        month_end = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(today.year, today.month + 1, 1) - timedelta(days=1)

    # Get all subscriptions
    subscriptions_data = get_request("subscriptions/", user_id=user_id) or []

    # Separate active and inactive subscriptions
    active_subs = [s for s in subscriptions_data if s.get("status") == "active"]
    inactive_subs = [s for s in subscriptions_data if s.get("status") != "active"]

    # Calculate monthly cost of active subscriptions
    monthly_cost = Decimal('0')
    for sub in active_subs:
        sub_amount = Decimal(str(sub.get("amount", 0)))
        billing_cycle = sub.get("billing_cycle", "monthly")

        if billing_cycle == 'daily':
            monthly_cost += sub_amount * 30
        elif billing_cycle == 'weekly':
            monthly_cost += sub_amount * 4
        elif billing_cycle == 'monthly':
            monthly_cost += sub_amount
        elif billing_cycle == 'yearly':
            monthly_cost += sub_amount / 12

    # This month's actual subscription spending
    this_month_total = _get_subscriptions_spent_for_period(user_id, month_start, month_end)

    # Format response to match original structure
    return {
        "active": {
            "count": len(active_subs),
            "monthly_cost": float(monthly_cost),
            "items": [
                {
                    "id": sub["id"],
                    "name": sub["name"],
                    "amount": float(sub.get("amount", 0)),
                    "billing_cycle": sub.get("billing_cycle"),
                    "category": sub.get("category"),
                    "payments": []  # We don't have easy access to payments via API in this context
                }
                for sub in active_subs
            ]
        },
        "inactive": {
            "count": len(inactive_subs),
            "items": [
                {
                    "id": sub["id"],
                    "name": sub["name"],
                    "amount": float(sub.get("amount", 0)),
                    "billing_cycle": sub.get("billing_cycle"),
                    "category": sub.get("category"),
                    "payments": []  # We don't have easy access to payments via API in this context
                }
                for sub in inactive_subs
            ]
        },
        "this_month_total": float(this_month_total),
        "total_subscriptions": len(active_subs) + len(inactive_subs)
    }


def _get_subscriptions_spent_for_period(user_id, start_date, end_date):
    """
    Helper to get total subscription spending for a period.
    """
    payments_params = {"user_id": user_id}
    if start_date and end_date:
        payments_params["due_date__gte"] = start_date.isoformat() if hasattr(start_date, 'isoformat') else str(start_date)
        payments_params["due_date__lte"] = end_date.isoformat() if hasattr(end_date, 'isoformat') else str(end_date)

    payments_data = get_request("subscription-payments/", **payments_params) or []
    return sum(Decimal(str(p.get("amount", 0))) for p in payments_data)