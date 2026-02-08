from ..models import Budget, Transaction, Subscription
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from decimal import Decimal
from .date_filter import filter_queryset_by_period
from .spending_calculations import get_subscription_amount_for_period


def reset_expired_budgets(user):
    """Check and reset expired budgets, creating new ones if recurring."""
    today = date.today()

    expired = Budget.objects.filter(
        user=user,
        is_active=True,
        period_end__lt=today
    )

    created_budgets = []

    for budget in expired:
        # Deactivate the expired budget
        budget.is_active = False
        budget.save(update_fields=["is_active"])

        # Skip if not recurring
        if not budget.is_recurring:
            continue
        
        # Calculate next period based on recurrence type
        next_start, next_end = calculate_next_period(
            budget.period_end,
            budget.recurrence
        )

        # Create new budget
        new_budget = Budget.objects.create(
            user=budget.user,
            category=budget.category,
            amount=budget.amount,
            period_start=next_start,
            period_end=next_end,
            recurrence=budget.recurrence,
            is_active=True,
            is_recurring=True,
            is_shared=budget.is_shared,
        )
        created_budgets.append(new_budget)

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
    return Transaction.objects.filter(
        user=budget.user,
        category=budget.category,
        date__gte=budget.period_start,
        date__lte=budget.period_end,
    )

def get_subscriptions_for_budget(budget):
    """Get all subscriptions that match a budget's category"""
    return Subscription.objects.filter(
        user=budget.user,
        category__iexact=budget.category,
        status='active'
    )


def compute_budget_spent(budget):
    """Caclulate total spent for a budget."""
    transaction_result = get_transactions_for_budget(budget).aggregate(total=Sum("amount"))
    transaction_total = transaction_result["total"] or Decimal('0')

    # Subscription total for the budget period
    subscription_total = Decimal('0')
    subscriptions = get_subscriptions_for_budget(budget)
    for subscription in subscriptions:
        subscription_total += get_subscription_amount_for_period(
            subscription,
            budget.period_start,
            budget.period_end
        )

    return {
        "total": float(transaction_total + subscription_total),
        "transactions": float(transaction_total),
        "subscriptions": float(subscription_total),
    }


def toggle_budget_recurring(budget_id, user, is_recurring):
    """Toggle the recurring status of a budget."""
    try:
        budget = Budget.objects.get(id=budget_id, user=user)
        budget.is_recurring = is_recurring
        budget.save(update_fields=["is_recurring"])
        return {"success": True, "budget": budget}
    except Budget.DoesNotExist:
        return {"success": False, "error": "Budget not found."}
    
def update_budget(budget_id, user, data):
    """Update a budget with provided data."""
    try:
        budget = Budget.objects.get(id=budget_id, user=user)

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

        for field in allowed_fields:
            if field in data:
                setattr(budget, field, data[field])

        budget.save()
        return {"success": True, "budget": budget}
    except Budget.DoesNotExist:
        return {"success": False, "error": "Budget not found."}

def stop_budget_recurring(budget_id, user):
    """Stop a budget from recurring."""
    return toggle_budget_recurring(budget_id, user, is_recurring=False)

def start_budget_recurring(budget_id, user, recurrence="monthly"):
    """Start a budget as recurring."""
    try:
        budget = Budget.objects.get(id=budget_id, user=user)
        budget.is_recurring = True
        budget.recurrence = recurrence
        budget.save(update_fields=["is_recurring", "recurrence"])
        return {"success": True, "budget": budget}
    except Budget.DoesNotExist:
        return {"success": False, "error": "Budget not found."}

