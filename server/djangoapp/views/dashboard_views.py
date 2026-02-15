
from django.db.models import Sum
from django.http import JsonResponse
import json
import logging
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .budgets_views import get_budgets_data
from .incomes_views import get_income_data

from ..services.budgets import (
    reset_expired_budgets,
    compute_budget_spent,
    get_transactions_for_budget,
    update_budget,
    get_subscriptions_for_budget
)
from ..services.date_filter import (
    filter_queryset_by_period,
    get_period_label,
    get_period_display_dates
)
from ..services.transactions import get_transactions_chart_data
from ..services.category_service import compute_spending_by_category
from ..services.subscription_service import (
    get_subscriptions_for_period,
    compute_subscription_summary,
    compute_subscription_total
    )

logger = logging.getLogger(__name__)

def dashboard(request):
    # print(request.user)
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )

    period = request.GET.get("period", "monthly")

    if request.method == "GET":
        try:
            # transactions = filter_queryset_by_period(
            #         Transaction.objects.filter(user=request.user),
            #         period=period,
            #         date_field="date"
            # )

            transactions = get_transactions_chart_data(request.user, period)

            categories = compute_spending_by_category(request.user, period)

            from ..services.subscription_service import generate_subscription_payments
            generate_subscription_payments(request.user)

            subscriptions = get_subscriptions_for_period(request.user, period)

            budgets = get_budgets_data(request.user, period)

            income = get_income_data(request.user, period)

            return JsonResponse({
                "dashboard": {
                    "transactions": transactions,
                    "categories": categories,
                    "subscriptions": subscriptions,
                    "budgets": budgets,
                    "income": income,
                    "period": {
                        "value": period,
                        "label": get_period_label(period),
                        **get_period_display_dates(period)
                    },
                },
                "user": {
                    "id": request.user.id,
                    "username": request.user.username,
                    "is_authenticated": request.user.is_authenticated
                }
            })
        except Exception as e: 
            logger.error(f"Error fetching dashboard: {e}")
            return JsonResponse({"error": "Failed to fetch dashboard"}, status=500)