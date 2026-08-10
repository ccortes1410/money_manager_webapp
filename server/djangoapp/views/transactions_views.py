import json
import logging
from decimal import Decimal

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..restapi import get_request, post_request, patch_request, delete_request
from ..services.api_adapters import transaction_from_row
from ..services.date_filter import get_date_bounds

logger = logging.getLogger(__name__)

def _iso_date(dt):
    """Normalize a datetime or date into a plain YYYY-MM-DD string."""
    return dt.date().isoformat() if hasattr(dt, "date") else dt.isoformat()

def get_transactions_data(user, period):
    """Get transaction summary for dashboard."""
    start, end = get_date_bounds(period)

    transaction_params = {"user_id": user.id}

    if start and end:
        transaction_params["date__gte"]: _iso_date(start)
        transaction_params["date__lte"]: _iso_date(end)
    # Get transactions for the period
    transactions = get_request("transactions/", **transaction_params) or []

    total_spent = sum((Decimal(str(t["amount"])) for t in transactions), Decimal('0'))

    return {
        "total_spent": float(total_spent),
        "count": len(transactions),
    }
    
def get_transactions(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )
    
    category = request.GET.get("category")

    if request.method != "GET":
        return JsonResponse(
            {"error": "Method Not Allowed"}, status=405
        )

    try:
        params = {"user_id": request.user.id}
        if category:
            params["category"] = category

        rows = get_request("transactions/", **params) or []
        transactions = [transaction_from_row(r) for r in rows]
        transactions.sort(key=lambda t: t.date, reverse=True)

        transactions_data = []
        for transaction in transactions:
            transactions_data.append({
                "id": transaction.id,
                "amount": float(transaction.amount),
                "date": transaction.date.isoformat() if transaction.date else None,
                "description": transaction.description,
                "category": transaction.category
            })

        return JsonResponse({
            "transactions": transactions_data,
            "user": {
                "id": request.user.id,
                "username": request.user.username,
                "is_authenticated": request.user.is_authenticated,
            }
        })
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        return JsonResponse({"error": "Failed to fetch transactions"}, status=500)

@csrf_exempt
def transaction_create(request):
    """Create a new transaction."""
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )
    
    if request.method != "POST":
        return JsonResponse(
            {"error": "Method Not Allowed"}, status=405
        )
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON"}, status=400
        )
    
    required_fields = ["amount", "description", "category", "date"]
    for field in required_fields:
        if field not in data:
            return JsonResponse(
                {"error": f"Missing field: {field}"}, status=400
            )

    row = post_request("transactions/", {
        "user_id": request.user.id,
        "amount": str(data["amount"]), # Convert to string for API
        "description": data["description"],
        "date": data["date"],
    })

    if not row:
        return JsonResponse(
            {"error": "Failed to create transaction."}, status=500
        )

    transaction = transaction_from_row(row)

    return JsonResponse({
        "message": "Transaction created successfully",
        "transaction": {
            "id": transaction.id,
            "category": transaction.category,
            "amount": float(transaction.amount),
            "date": transaction.date.isoformat() if transaction.date else None,
            "description": transaction.description,
        },
        "user": {
            "id": request.user.id,
            "username": request.user.username,
            "is_authetincated": request.user.is_authenticated
        }
    }, status=201)

@csrf_exempt
@require_http_methods(["PATCH"])
def transaction_update(request, transaction_id):
    """Update transaction details."""
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON"}, status=400
        )
    # First verify the transaction belongs to the user
    row = get_request(f"transactions/{transaction_id}")
    if not row or row["user_id"] != request.user.id:
        return JsonResponse(
            {"error": "Transaction not found"}, status=404
        )
    # Prepare update payload (only allow certain fields)
    allowed_fields = ["amount", "description", "category", "date"]
    payload = {}
    for field in allowed_fields:
        if field in data:
            # Convert amount to string for API compatibility
            if field == "amount":
                payload[field] = str(data[field])
            else:
                payload[field] = data[field]

    if not payload:
        return JsonResponse(
            {"error": "No valid fields to update"}, status=400
        )

    updated = patch_request(f"transactions/{transaction_id}", payload)
    if not updated:
        return JsonResponse(
            {"error": "Failed to update transaction"}, status=500
        )

    transaction = transaction_from_row(updated)

    return JsonResponse({
        "message": "Transactions updated successfully",
        "transactions": {
            "id": transaction.id,
            "category": transaction.category,
            "amount": float(transaction.amount),
            "date": transaction.date.isoformat() if transaction.date else None,
            "description": transaction.description,
        },
        "user": {
            "id": request.user.id,
            "username": request.user.username,
            "is_authenticated": request.user.is_authenticated,
        }
    })
    
@csrf_exempt
def transaction_delete(request):
    """Delete transactions."""
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )
    
    if request.method != "DELETE":
        return JsonResponse(
            {"error": "Method not allowed"}, status=405
        )
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON"}, status=400
        )
    
    transaction_ids = data.get("ids", [])
    if not transaction_ids:
        return JsonResponse(
            {"error": "No transaction IDs provided"}, status=400
        )
    
    # Verify each transaction belongs to the user before deleting
    for tid in transaction_ids:
        row = get_request(f"transactions/{tid}")
        if not row or row["user_id"] != request.user.id:
            return JsonResponse(
                {"error": f"Transaction {tid} not found or access denied"}, status=404
            )
    # Delete each transaction
    deleted_count = 0
    for tid in transaction_ids:
        result = delete_request(f"transactions/{tid}")
        if result is not None: # Successful deletion
            deleted_count += 1

    return JsonResponse({
        "message": f"Deleted {deleted_count} transaction record(s).",
        "deleted_count": deleted_count,
        "user": {
            "id": request.user.id,
            "username": request.user.username,
            "is_authenticated": request.user.is_authenticated,
        }
    })
