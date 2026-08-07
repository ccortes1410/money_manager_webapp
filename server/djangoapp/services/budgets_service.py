from datetime import date, timedelta
from decimal import Decimal
from dateutil.relativedelta import relativedelta

from ..restapi import get_request, post_request, patch_request, delete_request
from .api_adapters import budget_from_row, transaction_from_row, subscription_from_row
from .spending_calculations import get_subscription_amount_for_period


def reset_expired_budgets(user):
    """Check and reset expired budgets, creating new ones if recurring."""
    today = date.today()

    rows = get_request(
        "budget/",
        user_id=user.id,
        period_end__lte=today.isoformat(),
    ) or []
    # NOTE: filtering booleans (is_active) through the generic API's query
    # params is unreliable (MySQL boolean coercion of the string "true"
    # isn't guaranteed), so we filter it here in Python instead.

    expired = [budget_from_row(r) for r in rows if r["is_active"]]

    created_budgets = []

    for budget in expired:
        # Deactivate the expired budget
        patch_request(f"budget/{budget.id}", {"is_active": False})

        # Skip if not recurring
        if not budget.is_recurring:
            continue
        
        # Calculate next period based on recurrence type
        next_start, next_end = calculate_next_period(
            budget.period_end,
            budget.recurrence
        )

        # Create new budget
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
        })
        # NOTE: the (category, user) unique_together constraint still
        # exists on this table (enforced by Sequelize now instead of
        # Django). A colliding create returns None here rather than
        # raising IntegrityError -- restapi.post_request swallows HTTP
        # error responses and logs them instead of propagating an
        # exception. Any test asserting IntegrityError against this path
        # will need to change to asserting `created_budgets == []` instead.
        if new_row:
            created_budgets.append(budget_from_row(new_row))

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
        category=budget.category,
        date__gte=budget.period_start.isoformat(),
        date__lte=budget.period_end.isoformat(),
    ) or []
    return [transaction_from_row(r) for r in rows]


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
    """Caclulate total spent for a budget."""
    transactions = get_transactions_for_budget(budget)
    transaction_total = sum((t.amount for t in transactions), Decimal("0"))

    # Subscription total for the budget period
    subscription_total = Decimal("0")
    for subscription in get_subscriptions_for_budget(budget):
        subscription_total += get_subscription_amount_for_period(
            subscription,
            budget.period_start,
            budget.period_end
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

