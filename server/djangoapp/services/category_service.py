from ..models.models import Transaction, Subscription, SubscriptionPayment
from .date_filter import filter_queryset_by_period
from django.db.models import Sum
from collections import defaultdict

def compute_spending_by_category(user, period: str):
    """Combines transactions and subscription payments by category"""
    category_totals = []

    # Get transactions totals by category
    tx_queryset = filter_queryset_by_period(
        Transaction.objects.filter(user=user),
        period=period,
        date_field="date"
    )

    tx_by_category = tx_queryset.values(
        "category"
    ).annotate(
        total=Sum("amount")
    )

    payments = filter_queryset_by_period(
        SubscriptionPayment.objects.filter(subscription__user=user),
        period=period,
        date_field="date"
    )

    payment_by_category = payments.values(
        "subscription__category"
    ).annotate(total=Sum('amount'))

    category_totals = defaultdict(lambda: {
        "transactions": 0,
        "subscriptions": 0,
        "total": 0
    })

    for item in tx_by_category:
        category = item["category"] or "Uncategorized"
        amount = float(item["total"] or 0)
        category_totals[category]["transactions"] += amount
        category_totals[category]["total"] += amount

    for item in payment_by_category:
        category = item["subscription__category"] or "Uncategorized"
        amount = float(item["total"] or 0)
        category_totals[category]["subscriptions"] += amount
        category_totals[category]["total"] += amount

    grand_total = sum(cat["total"] for cat in category_totals.values())

    result = [
        {
            "category": category,
            "total": data["total"],
            "transactions": data["transactions"],
            "subscriptions": data["subscriptions"],
            "percentage": round((data["total"] / grand_total) * 100, 1) if grand_total > 0 else 0
        }
        for category, data in category_totals.items()
    ]

    result.sort(key=lambda x: x["total"], reverse=True)

    return {
            "categories": result,
            "total": grand_total,
            "transaction_total": sum(cat["transactions"] for cat in result),
            "subscription_total": sum(cat["subscriptions"] for cat in result)
        }