from datetime import date, datetime, timedelta
from calendar import monthrange
from decimal import Decimal
from ..restapi import get_request, post_request, patch_request, delete_request
from .date_filter import get_date_bounds


def generate_subscription_payments(user_id, up_to_date=None):
    """
    Generate SubscriptionPayment records for all active subscriptions
    up to the specified date (default: today).

    This function calls the Node.js backend API to generate payments.
    Existing payments (including ones manually marked as unpaid) are preserved.
    """
    if up_to_date is None:
        up_to_date = date.today()

    return _generate_subscription_payments_via_api(user_id, up_to_date)


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
        start_date = _parse_api_date(sub_data["start_date"])
        end_date = _parse_api_date(sub_data.get("end_date"))
        amount = Decimal(str(sub_data["amount"]))
        billing_cycle = sub_data["billing_cycle"]
        billing_day = int(sub_data["billing_day"])

        # Handle clock skew if client browser date (start_date) is ahead of server date.today()
        effective_up_to = max(up_to_date, start_date) if start_date else up_to_date

        # Generate payments for this subscription
        created_count += _generate_payments_for_subscription_via_api(
            user_id, subscription_id, start_date, end_date, amount,
            billing_cycle, billing_day, effective_up_to
        )

    return created_count


def _parse_api_date(value):
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value.split("T", 1)[0])
    raise ValueError(f"Invalid subscription date: {value!r}")


def _generate_payments_for_subscription_via_api(user_id, subscription_id, start_date, end_date,
                                               amount, billing_cycle, billing_day, up_to_date):
    """
    Generate all missing SubscriptionPayment records for a subscription
    from start_date to up_to_date, and remove off-schedule or duplicate rows.
    """
    created_count = 0

    # Get all valid billing dates from start to up_to_date
    billing_dates = [
        d for d in get_billing_dates(
            start_date=start_date,
            end_date=up_to_date,
            billing_cycle=billing_cycle,
            billing_day=billing_day
        )
        if not (end_date and d > end_date)
    ]
    valid_due_dates = {d.isoformat() for d in billing_dates}

    # Reconcile existing payments for this subscription
    all_existing = get_request("subscription-payments/", subscription_id=subscription_id) or []
    existing_by_date = set()
    for p in all_existing:
        due = _parse_api_date(p.get("due_date"))
        due_iso = due.isoformat() if due else None
        if not due_iso or due_iso not in valid_due_dates or due_iso in existing_by_date:
            if p.get("id") is not None:
                delete_request(f"subscription-payments/{p['id']}")
        else:
            existing_by_date.add(due_iso)

    for billing_date in billing_dates:
        due_iso = billing_date.isoformat()

        # If no payment exists for this date, create one (auto-marked as paid when due)
        if due_iso not in existing_by_date:
            is_due = billing_date <= up_to_date
            payment_data = {
                "user_id": user_id,
                "subscription_id": subscription_id,
                "due_date": due_iso,
                "amount": str(amount),
                "is_paid": is_due,
                "paid_date": due_iso if is_due else None,
                "created_at": datetime.now().isoformat(),
            }

            response = post_request("subscription-payments/", payment_data)
            if response and "error" not in response:
                created_count += 1
                existing_by_date.add(due_iso)

    return created_count


def get_first_billing_date(start_date, billing_cycle, billing_day=1, end_date=None):
    """
    Determine the first billing date on or after start_date.
    For monthly subscriptions, aligns to billing_day in start_date's month
    (or the next month if billing_day has already passed in start_date's month,
    unless start_date is in the current target month so a newly created
    subscription gets its current month's payment).
    """
    if billing_cycle == "monthly":
        max_day = monthrange(start_date.year, start_date.month)[1]
        day = min(max(1, int(billing_day)), max_day)
        candidate = start_date.replace(day=day)
        if candidate >= start_date:
            return candidate
        if end_date and (start_date.year, start_date.month) == (end_date.year, end_date.month) and candidate <= end_date:
            return candidate
        return get_next_billing_date(start_date, "monthly", billing_day)
    return start_date


def get_billing_dates(start_date, end_date, billing_cycle, billing_day=1):
    """
    Calculate all billing dates between start_date and end_date.
    """
    dates = []
    current = get_first_billing_date(start_date, billing_cycle, billing_day, end_date=end_date)

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

    payments_data = [
        p for p in (get_request("subscription-payments/", **payments_params) or [])
        if p.get("is_paid", True)
    ]

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
        sub_id = payment.get("subscription_id") or payment.get("subscription")
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

    payments_data = [
        p for p in (get_request("subscription-payments/", **payments_params) or [])
        if p.get("is_paid", True)
    ]
    return sum(Decimal(str(p.get("amount", 0))) for p in payments_data)