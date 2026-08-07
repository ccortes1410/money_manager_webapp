"""
Seeds the database with sample data for local development.

Usage:
    python manage.py shell -c "from djangoapp.populate import initiate; intiate()
    
or run directly:
    python djangoapp/populate.py
"""
import os
import sys
from datetime import date, timedelta
from decimal import Decimal

import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoproj.settings")
django.setup()

from django.contrib.auth.models import User # noqa: E402
from djangoapp.models.models import ( #noaq: E402
    Transaction,
    Budget,
    Subscription,
    SubscriptionPayment,
    Income,
    SharedBudget,
    SharedBudgetMember,
    SharedExpense
)
from djangoapp.models.friendship import Friendship # noqa: E402


def get_or_create_user(username, password, **extra_fields):
    """Create a user with a properly hashed password (or return the existing one)."""
    user, created = User.objects.get_or_create(username=username, defaults=extra_fields)
    if created:
        user.set_password(password)
        user.save()
    return user


def initiate():
    today = date.today()
    month_start = today.replace(day=1)
    if today.month == 12:
        month_end = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(today.year, today.month + 1, 1) - timedelta(days=1)

    # ---- Users ----
    krlp = get_or_create_user("Alex", "password123", email="alex@example.com")
    alice = get_or_create_user("Alice", "password123", email="alice@example.com")
    bob = get_or_create_user("Bob", "password123", email="bob@example.com")

    # ---- Budgets (Krlp) ----
    budgets_data = [
        {"category": "Food", "amount": Decimal("100000")},
        {"category": "Housing", "amount": Decimal("450000")},
        {"category": "Entertainment", "amount": Decimal("50000")},
    ]
    for b in budgets_data:
        Budget.objects.update_or_create(
            user=krlp,
            category=b["category"],
            defaults={
                "amount": b["amount"],
                "period_start": month_start,
                "period_end": month_end,
                "recurrence": "monthly",
                "is_active": True,
                "is_recurring": True,
                "is_shared": False,
            },
        )

    # ---- Transactions (Krlp) ----
    transactions_data = [
        {"amount": Decimal("12000"), "description": "Grocery Shopping", "category": "Food", "date": today - timedelta(days=2)},
        {"amount": Decimal("450000"), "description": "Rent", "category": "Housing", "date": month_start},
        {"amount": Decimal("8000"), "description": "Movie Night", "category": "Entertainment", "date": today - timedelta(days=5)},
        {"amount": Decimal("6000"), "description": "Utilities", "category": "Housing", "date": today - timedelta(days=10)},
    ]
    for t in transactions_data:
        Transaction.objects.get_or_create(
            user=krlp, description=t["description"], date=t["date"], defaults=t
        )

    # ---- Subscription + a couple of payments each (Krlp) ----
    subscriptions_data = [
        {"name": "Netflix", "amount": Decimal("10900"), "category": "Entertainment", "billing_day": 15},
        {"name": "Gym", "amount": Decimal("29900"), "category": "Health", "billing_day": 1},
    ]
    for s in subscriptions_data:
        sub, _ = Subscription.objects.update_or_create(
            user=krlp,
            name=s["name"],
            defaults={
                "amount": s["amount"],
                "category": s["category"],
                "billing_cycle": "monthly",
                "billing_day": s["billing_day"],
                "start_date": today - timedelta(days=90),
                "status": "active",
            },
        )
        # One already-paid payment, one upcoming/unpaid.
        SubscriptionPayment.objects.get_or_create(
            subscription=sub,
            due_date=month_start,
            defaults={"amount": sub.amount, "is_paid": True, "paid_date": month_start},
        )
        SubscriptionPayment.objects.get_or_create(
            subscription=sub,
            due_date=month_end,
            defaults={"amount": sub.amount, "is_paid": False},
        )

    # ---- Income (Krlp) ----
    Income.objects.get_or_create(
        user=krlp,
        source="Salary",
        date_received=month_start,
        defaults={"amount": Decimal("1500000"), "period_start": month_start, "period_end": month_end},
    )

    # ---- Friendships ----
    Friendship.objects.get_or_create(sender=krlp, receiver=alice, defaults={"status": "accepted"})
    Friendship.objects.get_or_create(sender=bob, receiver=krlp, defaults={"status": "pending"})

    # ---- A shared budget with an equally-split expense ----
    shared_budget, _ = SharedBudget.objects.get_or_create(
        name="Roommate Rent",
        created_by=krlp,
        defaults={
            "description": "Shared apartment costs",
            "total_amount": Decimal("600000"),
            "category": "Housing",
            "period_start": month_start,
            "period_end": month_end,
            "is_active": True,
            "default_split_type": "equal",
        },
    )
    SharedBudgetMember.objects.get_or_create(
        shared_budget=shared_budget, user=krlp,
        defaults={"role": "owner", "contribution_percentage": Decimal("50")},
    )
    SharedBudgetMember.objects.get_or_create(
        shared_budget=shared_budget, user=alice,
        defaults={"role": "editor", "contribution_percentage": Decimal("50")},
    )

    expense, created = SharedExpense.objects.get_or_create(
        shared_budget=shared_budget,
        description="August Rent",
        defaults={
            "amount": Decimal("300000"),
            "paid_by": krlp,
            "date": month_start,
            "category": "Housing",
            "created_by": krlp,
        },
    )
    if created:
        expense.create_equal_splits()

    print("Sample data created/updated successfully.")


if __name__ == "__main__":
    initiate()