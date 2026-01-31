from ..models import Budget, Transaction
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from .date_filter import filter_queryset_by_period


def reset_expired_budgets(user):
    today = date.today()

    expired = Budget.objects.filter(
        user=user,
        is_active=True,
        period_end__lt=today
    )

    for budget in expired:
        budget.is_active = False
        budget.save(update_fields=["is_active"])

        if not budget.is_recurring:
            continue

        if budget.recurrence == "weekly":
            next_start = budget.period_end + timedelta(days=1)
            next_end = next_start + timedelta(days=6)
        
        elif budget.recurrence == "monthly":
            next_start = budget.period_en + timedelta(days=1)
            next_end = next_start + relativedelta(months=1) - timedelta(days=1)
        
        elif budget.recurrence == "yearly":
            next_start = budget.period_end + timedelta(days=1)
            next_end = next_start + relativedelta(years=1) - timedelta(days=1)
        
        Budget.objects.create(
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

def get_transactions_for_budget(budget):
    return Transaction.objects.filter(
        user=budget.user,
        category=budget.category,
        date__gte=budget.period_start,
        date__lte=budget.period_end,
    )

def compute_budget_spent(budget):
    result = get_transactions_for_budget(budget).aggregate(total=Sum("amount"))

    return result["total"] or 0
