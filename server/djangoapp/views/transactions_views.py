from ..models.models import Transaction
from django.contrib.auth.models import User
from django.http import JsonResponse
import json
import logging

logger = logging.getLogger(__name__)

def get_transactions(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Unauthorized"}, status=401
        )
    
    category = request.GET.get("category")

    if request.method == "GET":
        if category:
            transactions = Transaction.objects.filter(user=request.user, category=category)
        else:
            transactions = Transaction.objects.filter(user=request.user)
        data = list(transactions.values())
        return JsonResponse({
            "transactions": data,
            "user": {
                "id": request.user.id,
                "username": request.user.username,
                "is_authenticated": request.user.is_authenticated
            }
        })
    
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            amount = data.get("amount")
            date = data.get("date")
            description = data.get("description")
            category = data.get("category")
            Transaction.objects.create(
                user=request.user,
                description=description,
                amount=amount,
                date=date,
                category=category
            )
            return JsonResponse({"status": "Transaction added successfully"}, status=201)
        except Exception as e:
            logger.error(f"Error adding transaction: {e}")
            return JsonResponse({"error": "Failed to add transaction"}, status=500)
    
    elif request.method == "DELETE":
        try:
            data = json.loads(request.body)
            ids = data.get("ids", [])
            Transaction.objects.filter(id__in=ids, user=request.user).delete()
            return JsonResponse({"status": "deleted"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)



def transaction_create(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error":"Invalid JSON"}, status=400)
    
    required_fields = ["amount", "description", "category", "date"]
    for field in required_fields:
        if field not in data:
            return JsonResponse({"error":f"Missing field: {field}"}, status=400)
        
    transaction = Transaction.objects.create(
        user=request.user,
        amount=data["amount"],
        description=data["description"],
        category=data["category"],
        date=data["date"],
    )
    return JsonResponse({
        "message": "Transaction created succesfully",
        "transaction": {
            "id": transaction.id,
            "category": transaction.category,
            "amount": transaction.amount,
        },
        "user": {
            "id": request.user.id,
            "username": request.user.username,
            "is_auhtetincated": request.user.is_authenticated
        }
    })


def transaction_update(request, transaction_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    if request.method != 'PATCH':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)

    from ..services.transactions import update_transaction

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"})
    
    result = update_transaction(transaction_id, request.user, data)

    if result["success"]:
        transaction = result["transaction"]
        return JsonResponse({
            "message": "Transaction updated successfully",
            "transaction": {
                "id": transaction.id,
                "category": transaction.category,
                "amount": float(transaction.amount),
                "date": transaction.date
            },
            "user": {
                "id": request.user.id,
                "username": request.user.username,
                "is_authenticated": request.user.is_authenticated
            }
        })
    else:
        error = result["error"]
        return JsonResponse({
            "message": "Error updating transaction",
            "error": error
        })


def transaction_delete(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    if request.method != 'DELETE':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    transaction_ids = data.get("ids", [])
    if not transaction_ids:
        return JsonResponse({"error": "No income Income IDs provided"})
    
    deleted_count = Transaction.objects.filter(
        id__in=transaction_ids,
        user=request.user
    ).delete()[0]

    # summary = compute_income_summary(request.user)
    print("Deleted transactions:", deleted_count)
    return JsonResponse({
        "message": f"Deleted {deleted_count} transaction record(s).",
        "deleted_count": deleted_count,
        # "summary": summary,
        "user": {
            "id": request.user.id,
            "username": request.user.username,
            "is_authenticated": request.user.is_authenticated
        }
    })