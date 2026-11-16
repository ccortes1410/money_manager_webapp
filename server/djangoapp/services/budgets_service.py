from datetime import date, timedelta
from decimal import Decimal
from dateutil.relativedelta import relativedelta

from ..restapi import get_request, post_request, patch_request, delete_request
from .api_adapters import budget_from_row, transaction_from_row, subscription_from_row
from .spending_calculations import get_subscription_amount_for_period


def reset_expired_budgets(user):
    """Check and reset expired budgets, creating new ones if recurring."""
    today = date.today()

    all_rows = get_request(
        "budgets/",
        user_id=user.id,
    ) or []
    all_budgets = [budget_from_row(r) for r in all_rows]

    # Categories that already have an active non-expired budget
    active_categories = {
        b.category.lower()
        for b in all_budgets
        if b.is_active and b.period_end > today
    }

    # Include active expired budgets, plus any recurring expired budgets that
    # were deactivated before their successor could be created.
    expired = [
        b for b in all_budgets
        if b.period_end <= today and (
            b.is_active or (b.is_recurring and b.category.lower() not in active_categories)
        )
    ]

    created_budgets = []

    for budget in expired:
        if not budget.is_recurring:
            if budget.is_active:
                patch_request(f"budgets/{budget.id}", {"is_active": False})
            continue

        if budget.category.lower() in active_categories:
            patch_request(f"budgets/{budget.id}", {"is_active": False, "is_recurring": False})
            continue

        # Calculate next period based on recurrence type, advancing until it covers today
        next_start, next_end = calculate_next_period(
            budget.period_end,
            budget.recurrence
        )
        while next_end <= today:
            next_start, next_end = calculate_next_period(
                next_end,
                budget.recurrence
            )

        # Deactivate the expired budget
        if budget.is_active:
            patch_request(f"budgets/{budget.id}", {"is_active": False})

        # Create new budget for the current period
        new_row = post_request("budgets/", {
            "user_id": budget.user_id,
            "category": budget.category,
            "amount": str(budget.amount),
            "period_start": next_start.isoformat(),
            "period_end": next_end.isoformat(),
            "recurrence": budget.recurrence,
            "is_active": True,
            "is_recurring": True,
            "is_shared": budget.is_shared,
            "created_at": today.isoformat(),
        })
        if new_row:
            patch_request(f"budgets/{budget.id}", {"is_active": False, "is_recurring": False})
            created_budgets.append(budget_from_row(new_row))
            active_categories.add(budget.category.lower())

    return created_budgets


def calculate_next_period(period_end, recurrence):
    """Calculate the next period start and end dates based on recurrence."""
    next_start = period_end + timedelta(days=1)
    
    if recurrence == "daily":
        next_end = next_start
    elif recurrence == "weekly":
        next_end = next_start + timedelta(days=6)
    elif recurrence == "monthly":
        next_end = next_start + relativedelta(months=1) - timedelta(days=1)
    elif recurrence == "yearly":
        next_end = next_start + relativedelta(years=1) - timedelta(days=1)
    else:
        # Deault to monthly if invalid recurrence
        next_end = next_start + relativedelta(months=1) - timedelta(days=1)

    return next_start, next_end


def get_transactions_for_budget(budget):
    """Get all transactions that fall within the budget's period and category."""
    rows = get_request(
        "transactions/",
        user_id=budget.user_id,
        date__gte=budget.period_start.isoformat(),
        date__lte=budget.period_end.isoformat(),
    ) or []
    return [
        transaction_from_row(r) for r in rows
        if (r.get("category") or "").lower() == budget.category.lower()
    ]


def get_subscriptions_for_budget(budget):
    """Get all subscriptions that match a budget's category"""
    rows = get_request(
        "subscriptions/",
        user_id=budget.user_id,
        status="active",
    ) or []

    return [
        subscription_from_row(r) for r in rows
        if r["category"].lower() == budget.category.lower()
    ]


def compute_budget_spent(budget):
    """Calculate total spent for a budget."""
    transactions = get_transactions_for_budget(budget)
    transaction_total = sum((t.amount for t in transactions), Decimal("0"))

    # Subscription total for the budget period from paid subscription payments
    matching_subs = get_subscriptions_for_budget(budget)
    matching_sub_ids = {s.id for s in matching_subs}

    subscription_total = Decimal("0")
    if matching_sub_ids:
        payment_rows = get_request(
            "subscription-payments/",
            user_id=budget.user_id,
            due_date__gte=budget.period_start.isoformat(),
            due_date__lte=budget.period_end.isoformat(),
        ) or []
        paid_matching_payments = [
            p for p in payment_rows
            if (p.get("subscription_id") or p.get("subscription")) in matching_sub_ids
            and p.get("is_paid", True)
        ]
        subscription_total = sum(
            (Decimal(str(p.get("amount", 0))) for p in paid_matching_payments),
            Decimal("0"),
        )

    total = transaction_total + subscription_total
    return {
        "total": float(total),
        "transactions": float(transaction_total),
        "subscriptions": float(subscription_total),
    }


def toggle_budget_recurring(budget_id, user, is_recurring):
    """Toggle the recurring status of a budget."""
    row = get_request(f"budgets/{budget_id}")
    if not row or row["user_id"] != user.id:
        return {"success": False, "error": "Budget not found."}

    updated = patch_request(f"budgets/{budget_id}", {"is_recurring": is_recurring})
    if not updated:
        return {"success": False, "error": "Failed to update budget."}

    return {"success": True, "budget": budget_from_row(updated)}

    
def update_budget(budget_id, user, data):
    """Update a budget with provided data."""
    row = get_request(f"budgets/{budget_id}")
    if not row or row["user_id"] != user.id:
        return {"success": False, "error": "Budget not found."}
    
    # Update allowed fields
    allowed_fields = [
        "category",
        "amount",
        "period_start",
        "period_end",
        "recurrence",
        "is_recurring",
        "is_shared",
    ]
    payload = {field: data[field] for field in allowed_fields if field in data}

    updated = patch_request(f"budgets/{budget_id}", payload)
    if not updated:
        return {"success": False, "error": "Failed to update budget."}
    
    return {"success": True, "budget": budget_from_row(updated)}


def stop_budget_recurring(budget_id, user):
    """Stop a budget from recurring."""
    return toggle_budget_recurring(budget_id, user, is_recurring=False)

def start_budget_recurring(budget_id, user, recurrence="monthly"):
    """Start a budget as recurring."""
    row = get_request(f"budgets/{budget_id}")
    if not row or row["user_id"] != user.id:
        return {"success": False, "error": "Budget not found."}

    updated = patch_request(f"budgets/{budget_id}", {
        "is_recurring": True,
        "recurrence": recurrence,
    })
    if not updated:
        return {"success": False, "error": "Failed to update budget."}

    return {"success": True, "budget": budget_from_row(updated)}

