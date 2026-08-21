from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from django.utils import timezone
from functools import wraps
import json

from ..restapi import get_request, post_request, patch_request, delete_request
from ..services.api_adapters import (
    shared_budget_from_row,
    shared_budget_member_from_row,
    shared_budget_invite_from_row,
    shared_expense_from_row,
    expense_split_from_row,
    settlement_from_row,
    shared_budget_notification_from_row,
    budget_from_row,
    transaction_from_row,
    subscription_from_row,
    subscription_payment_from_row,
    income_from_row,
    get_username,
    get_user_first_name,
    get_user_last_name,
    get_user_email,
    get_user_data
)
from ..services.date_filter import get_date_bounds


def login_required_json(view_func):
    """Decorator to check if user is authenticated."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper

def _iso_date(dt):
    """Normalize a datetime or date into a plain YYYY-MM-DD string."""
    return dt.date().isoformat() if hasattr(dt, "date") else dt.isoformat()
# ===================== HELPER FUNCTIONS FOR API DATA ===================

def get_member_data(member_row, budget_row=None):
    """Get member data from API rows."""
    budget = budget_row or get_budget_by_id(member_row["shared_budget"])

    # Get total paid by calculating expenses where this member paid
    total_paid = get_total_paid_by_member(member_row["user_id"], member_row["shared_budget"])

    # Get total owed by calculating splits for this member
    total_owed = get_total_owed_by_member(member_row["user_id"], member_row["shared_budget"])

    balance = total_paid - total_owed

    return {
        'id': member_row["id"],
        'user': {
            'id': member_row["user_id"],
            'username': get_username(member_row["user_id"]),
            'email': get_user_email(member_row["user_id"]),
            'first_name': get_user_first_name(member_row["user_id"]),
            'last_name': get_user_last_name(member_row["user_id"]),
        },
        'role': member_row["role"],
        'contribution_percentage': float(member_row["contribution_percentage"]),
        'joined_at': member_row.get("joined_at"),
        'total_paid': total_paid,
        'total_owed': total_owed,
        'balance': balance,
    }


def get_budget_data(budget_row, user_id=None):
    """Get budget data from API rows."""
    # Get total spent by getting all expenses for this budget
    total_spent = get_total_spent_for_budget(budget_row["id"])
    total_amount = float(budget_row["total_amount"])
    remaining = total_amount - total_spent
    progress = (total_spent / total_amount * 100) if total_amount > 0 else 0

    # Get members
    members_data = get_budget_members(budget_row["id"])

    # Get current user's role and balance
    user_role = None
    user_balance = 0
    if user_id:
        member = next((m for m in members_data if m['user']['id'] == user_id), None)
        if member:
            user_role = member["role"]
            user_balanace = float(member["balance"])

    return {
        'id': budget_row["id"],
        'name': budget_row["name"],
        'description': budget_row["description"],
        'total_amount': total_amount,
        'total_spent': total_spent,
        'remaining': remaining,
        'progress': progress,
        'category': budget_row["category"],
        'created_by': {
            'id': budget_row["created_by"],
            'username': get_username(budget_row["created_by"]),
        },
        'period_start': budget_row["period_start"],
        'period_end': budget_row["period_end"],
        'is_active': budget_row["is_active"],
        'default_split_type': budget_row["default_split_type"],
        'member_count': len(members_data),
        'members': members_data,
        'user_role': user_role,
        'user_balance': user_balance,
        'created_at': budget_row["created_at"],
    }


def get_budget_by_id(budget_id):
    """Get budget by ID from API."""
    return get_request(f"shared-budgets/{budget_id}")


def get_budget_members(budget_id):
    """Get all members for a budget."""
    member_rows = get_request("shared-budget-members/", shared_budget=budget_id) or []
    members_data = []
    for member_row in member_rows:
        member_data = get_member_data(member_row)
        members_data.append(member_data)
    return members_data


def get_total_paid_by_member(user_id, budget_id):
    """Get total amount paid by a member in a budget."""
    # Get expenses where this member paid
    expense_rows = get_request("shared-expenses/", shared_budget=budget_id, paid_by=user_id) or []
    total = sum(float(expense_row["amount"]) for expense_row in expense_rows)
    return total


def get_total_owed_by_member(user_id, budget_id):
    """Get total amount owed by a member in a budget."""
    # Get splits for this member in this budget that are not settled
    split_rows = get_request("expense-splits/", shared_budget=budget_id, user_id=user_id, is_settled=False) or []
    total = sum(float(split_row["amount_owed"]) for split_row in split_rows)
    return total


def get_total_spent_for_budget(budget_id):
    """Get total amount spent in a budget."""
    expense_rows = get_request("shared-expenses/", shared_budget=budget_id) or []
    total = sum(float(expense_row["amount"]) for expense_row in expense_rows)
    return total


def get_settlements_for_budget(budget_id, limit=10):
    """Get settlements for a budget."""
    settlement_rows = get_request("shared-expenses/", shared_budget=budget_id) or []
    # Sort by date descending and limit
    settlement_rows.sort(key=lambda x: x.get("date") or "", reverse=True)
    settlement_rows = settlement_rows[:limit]

    settlements_data = []
    for settlement_row in settlement_rows:
        settlements_data.append({
            'id': settlement_row["id"],
            'payer': {
                'id': settlement_row["payer"],
                'username': get_username(settlement_row["payer"]),
            },
            'receiver': {
                'id': settlement_row["receiver"],
                'username': get_username(settlement_row["receiver"]),
            },
            'amount': float(settlement_row["amount"]),
            'date': settlement_row.get("date"),
            'notes': settlement_row.get("notes", ""),
            'created_at': settlement_row.get("created_at"),
        })
    return settlements_data

# ============================= SHARED BUDGET CRUD ==========================

@csrf_exempt
@login_required_json
def get_shared_budgets(request):
    """Get all shared budgets the user is a member of."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)

    user = request.user

    try:
        # Get budgets where user is a member
        membership_rows = get_request("shared-budget-members/", user_id=user.id) or []
        budget_ids = [membership_row["shared_budget"] for membership_row in membership_rows]
    
        budgets_data = []
        active_budgets = []
        inactive_budgets = []

        for budget_id in budget_ids:
            budget_row = get_request(f"shared-budgets/{budget_id}")
            if budget_row:
                budget_data = get_budget_data(budget_row, user.id)
                if budget_row["is_active"]:
                    active_budgets.append(budget_data)
                else:
                    inactive_budgets.append(budget_data)

        # Get pending invites for the user
        invite_rows = get_request("shared-budget-invites/", invited_user=user.id, status='pending') or []
        invites_data = []
        for invite_row in invite_rows:
            budget_row = get_request(f"shared-budgets/{invite_row['shared_budget']}")
            budget_name = budget_row["name"] if budget_row else "Unknown Budget"
            budget_amount = float(budget_row["total_amount"]) if budget_row else 0

            invited_by_row = get_request(f"users/{invite_row['invited_by']}")
            invited_by_username = invited_by_row["username"] if invited_by_row else f"user_{invite_row['invited_by']}"

            invites_data.append({
                'id': invite_row["id"],
                'budget_name': budget_name,
                'budget_amount': budget_amount,
                'invited_by': {
                    'id': invite_row["invited_by"],
                    'username': invited_by_username,
                },
                'role': invite_row["role"],
                'message': invite_row["message"],
                'created_at': invite_row.get("created_at"),
            })

        return JsonResponse({
            'active_budgets': active_budgets,
            'inactive_budgets': inactive_budgets,
            'pending_invites': invites_data,
            'total_count': len(budgets_data),
            'active_count': len(active_budgets),
            'inactive_count': len(inactive_budgets),
        })
    except Exception as e:
        print(f"Error fetching shared budgets: {e}")
        return JsonResponse({'error': 'Failed to fetch shared budgets'}, status=500)


@csrf_exempt
@login_required_json
def get_shared_budget_detail(request, budget_id):
    """Get detailed info for a specific shared budget."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)

    user = request.user

    try:
        # Get budget
        budget_row = get_request(f"shared-budgets/{budget_id}")
        if not budget_row:
            return JsonResponse({'error': 'Shared budget not found'}, status=404)

        # Check if user is a member
        member_row = get_request("shared-budget-members/", shared_budget=budget_id, user_id=user.id)
        if not member_row:
            return JsonResponse({'error': 'You are not a member of this budget'}, status=403)
        
        # Get budget data
        budget_data = get_budget_data(budget_row, user.id)

        # Ger recent expenses (limit 20)
        expense_rows = get_request("shared-expenses/", shared_budget=budget_id) or []
        expense_rows.sort(key=lambda x: x.get("date") or "", reverse=True)
        expense_rows = expense_rows[:20]
        expenses_data = [get_expense_data(expense_row) for expense_row in expense_rows]

        # Get debts
        debts_data = get_budget_debts_data(budget_id)

        # Get settlements
        settlements_data = get_settlements_for_budget(budget_id)

        budget_data['expenses'] = expenses_data
        budget_data['debts'] = debts_data
        budget_data['settlements'] = settlements_data

        return JsonResponse(budget_data)
    except Exception as e:
        print(f"Error fetching shared budget detail: {e}")
        return JsonResponse({'error': 'Failed to fetch shared budget details'}, status=500)


@csrf_exempt
@login_required_json
def create_shared_budget(request):
    """Create a new shared budget."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    user = request.user

    # Validate required fields
    required_fields = ['name', 'total_amount', 'period_start', 'period_end']
    for field in required_fields:
        if not data.get(field):
            return JsonResponse({'error': f'{field} is required'}, status=400)

    try:
        total_amount = float(str(data['total_amount']))
        if total_amount <= 0:
            return JsonResponse({'error': 'Total amount must be positive'}, status=400)
    except Exception:
        return JsonResponse({'error': 'Invalid total amount'}, status=400)
    
    # Create the budget via API
    budget_row = post_request("shared-budgets/", {
        'name': data['name'],
        'description': data.get('description',''),
        'total_amount': str(total_amount),
        'category': data.get('category',''),
        'created_by': user.id,
        'start_date': data['period_start'],
        'end_date': data['period_end'],
        'default_split_type': data.get('split_type', 'equal'),
        'is_active': True,
    })

    if not budget_row:
        return JsonResponse({'error': 'Failed to create budget'}, status=500)

    # Add creator as owner via API
    member_row = post_request("shared-budget-members/", {
        'shared_budget': budget_row["id"],
        'user_id': user.id,
        'role': 'owner',
        'contribution_percentage': 100,
    })

    if not member_row:
        return JsonResponse({'error': 'Failed to add owner to budget'}, status=500)

    # Send invites to friends if provided
    invited_friends = data.get('invite_friends', [])
    invites_sent = 0

    for friend_data in invited_friends:
        friend_id = friend_data.get('user_id') if isinstance(friend_data, dict) else friend_data

        try:
            # Verify friend exists
            friend_row = get_request(f"users/{friend_id}")
            if not friend_row:
                continue

            # Verify they are friends via API
            friendship_check = get_request(
                "friendships/",
                sender=user.id,
                receiver=friend_row["id"],
                status='accepted'
            ) or []
            reverse_check = get_request(
                "friendships/",
                sender=friend_row["id"],
                receiver=user.id,
                status='accepted'
            ) or []
            if not (friendship_check or reverse_check):
                continue

            # Create invite via API
            role = friend_data.get('role', 'editor') if isinstance(friend_data, dict) else 'editor'
            message = data.get('invite_message', f'{user.username} invited you to "{budget_row["name"]}"')

            invite_row = post_request("shared-budget-invites/", {
                'shared_budget': budget_row["id"],
                'invited_by': user.id,
                'invited_user': friend_id,
                'role': role,
                'message': message,
            })

            # Create notification via API
            post_request("shared-budget-notifications/", {
                'user_id': friend_id,
                'from_user_id': user.id,
                'notification_type': 'budget_invite',
                'shared_budget_id': budget_row["id"],
                'message': f'{user.username} invited you to shared budget "{budget_row["name"]}"'
            })

            invites_sent += 1
        except Exception as e:
            print(f"Error processing invite for friend {friend_id}: {e}")
            continue

    budget_data = get_budget_data(budget_row, user.id)

    return JsonResponse({
        'message': 'Shared budget created successfully',
        'budget': budget_data,
        'invites_sent': invites_sent,
    }, status=201)


@csrf_exempt
@login_required_json
def update_shared_budget(request, budget_id):
    """Update a shared budget."""
    if request.method not in ['PUT', 'PATCH']:
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    user = request.user

    try:
        # Verify budget exists and user has permission
        budget_row = get_request(f"shared-budgets/{budget_id}")
        if not budget_row:
            return JsonResponse({'error': 'Shared budget not found'}, status=404)

        # Check if user can edit (owner or editor)
        member_row = get_request("shared-budget-members/", shared_budget=budget_id, user_id=user.id)
        if not member_row or member_row["role"] not in ['owner', 'editor']:
            return JsonResponse({'error': 'You do not have permission to edit this budget'}, status=403)

        # Prepare update payload
        payload = {}
        if 'name' in data:
            payload['name'] = data['name']
        if 'description' in data:
            payload['description'] = data['description']
        if 'total_amount' in data:
            try:
                payload['total_amount'] = str(float(data['total_amount']))
            except Exception:
                return JsonResponse({'error': 'Invalid total amount'}, status=400)
        if 'category' in data:
            payload['category'] = data['category']
        if 'period_start' in data:
            payload['period_start'] = data['period_start']
        if 'period_end' in data:
            payload['period_end'] = data['period_end']
        if 'is_active' in data:
            payload['is_active'] = data['is_active']
        if 'default_split_type' in data:
            payload['default_split_type'] = data['default_split_type']

        if not payload:
            return JsonResponse({'error': 'No valid fields to update'}, status=400)

        # Update via API
        updated_budget_row = patch_request(f"shared-budgets/{budget_id}", payload)
        if not updated_budget_row:
            return JsonResponse({'error': 'Failed to updated budget'}, status=500)

        # Notify members
        post_request("shared-budget-notifications/", {
            'user_id': [m["user_id"] for m in get_budget_members(budget_id) if m["user"]["id"] != user.id],
            'fromn_user_id': user.id,
            'notification_type': 'budget_updated',
            'shared_budget_id': budget_id,
            'message': f'{user.username} updated budget "{updated_budget_row["name"]}"'
        })

        budget_data = get_budget_data(updated_budget_row, user.id)

        return JsonResponse({
            'message': 'Budget updated successfully',
            'budget': budget_data,
        })
    except Exception as e:
        print(f"Error updating shared budget: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required_json
def delete_shared_budget(request, budget_id):
    """Delete a shared budget."""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    user = request.user

    try:
        # Verify budget exists and user has permission (only owner can delete)
        budget_row = get_request(f"shared-budgets/{budget_id}")
        if not budget_row:
            return JsonResponse({'error': 'Shared budget not found'}, status=404)

        member_row = get_request("shared-budget_members/", shared_budget=budget_id, user_id=user.id)
        if not member_row or member_row["role"] != 'owner':
            return JsonResponse({'error': 'Only the owner can delete this budget'}, status=403)

        budget_name = budget_row["name"]

        # Delete via API
        result = delete_request(f"shared-budgets/{budget_id}")
        if result is None:
            return JsonResponse({'error': 'Failed to delete budget'}, status=500)

        return JsonResponse({
            'message': f'Budget "{budget_name}" deleted succesfully'
        })
    except Exception as e:
        print(f"Error deleting shared budget: {e}")
        return JsonResponse({'error': 'Failed to delete budget'}, status=500)


# ======================= INVITE MANAGEMENT ===============================

@csrf_exempt
@login_required_json
def invite_to_budget(request, budget_id):
    """Invite a friend to a shared budget."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    user = request.user

    try:
        # Verify budget exists
        budget_row = get_request(f"shared-budgets/{budget_id}")
        if not budget_row:
            return JsonResponse({'error': 'Shared budget not found'}, status=404)

        # Check if user can invite (must be owner or editor)
        member_row = get_request("shared-budget-members/", shared_budget=budget_id, user_id=user.id)
        if not member_row or member_row["role"] not in ['owner', 'editor']:
            return JsonResponse({'error': 'You do not have permission to invite members'}, status=403)

        friend_id = data.get('user_id')
        if not friend_id:
            return JsonResponse({'error': 'user_id is required'}, status=400)

        # Verify friend exists
        friend_row = get_request(f"users/{friend_id}")
        if not friend_row:
            return JsonResponse({'error': 'User not found'}, status=404)

        # Verify they are friends via API
        friendship_check = get_request(
            "friendships/",
            sender=user.id,
            receiver=friend_row["id"],
            status='accepted'
        ) or []
        reverse_check = get_request(
            "friendships/",
            sender=friend_row["id"],
            receiver=user.id,
            status='accepted'
        ) or []
        if not (friendship_check or reverse_check):
            return JsonResponse({'error': 'You can only invite friends'}, status=400)

        # Check if already a pending invite
        existing_invite = get_request("shared-budget-invites/", shared_budget=budget_id, invited_user=friend_id, status='pending')
        if existing_invite and len(existing_invite) > 0:
            return JsonResponse({'error': 'An invite has already been sent to this user'}, status=400)

        # Create invite via API
        role = data.get('role', 'editor')
        message = data.get('message', f'{user.username} invited you to "{budget_row["name"]}"')

        invite_row = post_request("shared-budget-invites/", {
            'shared_budget': budget_id,
            'invited_by': user.id,
            'invited_user': friend_id,
            'role': role,
            'message': message,
        })

        # Create notification via API
        post_request("shared-budget-notifications/", {
            'user_id': friend_id,
            'from_user_id': user.id,
            'notification_type': 'budget_invite',
            'shared_budget_id': budget_id,
            'message': f'{user.username} invited you to shared budget "{budget_row["name"]}"'
        })

        return JsonResponse({
            'message': f'Invitation sent to {friend_row["username"]}',
            'invite': {
                'id': invite_row["id"],
                'invited_user': {
                    'id': friend_id,
                    'username': friend_row["username"],
                },
                'role': invite_row["role"],
                'status': invite_row["status"]
            }
        }, status=201)
    except Exception as e:
        print(f"Error inviting to budget: {e}")
        return JsonResponse({'error': 'Failed to send invitation'}, status=500)


@csrf_exempt
@login_required_json
def respond_to_budget_invite(request, invite_id):
    """Accept or decline a budget invitation."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    user = request.user
    action = data.get('action')

    if action not in ['accept', 'decline']:
        return JsonResponse({'error': 'Invalid action. Use "accept" or "decline"'}, status=400)
    
    try:
        # Get invite and verify it's for the current user
        invite_rows = get_request("shared-budget-invites/", id=invite_id, invited_user=user.id, status='pending')
        if not invite_rows or len(invite_rows) == 0:
            return JsonResponse({'error': 'Invitation not found'}, status=404)

        invite_row = invite_rows[0]

        if action == 'accept':
            # Accept the invite via API
            updated_invite_row = patch_request(f"shared-budget-invites/{invite_id}", {'status': 'accepted'})
            if not updated_invite_row:
                return JsonResponse({'error': 'Failed to accept invitation'}, status=500)

            # Add user as member with appropriate role
            # For equal split, we need to update all members' contributions
            budget_id = invite_row["shared-budget"]
            budget_row = get_request(f"shared-budgets/{budget_id}")

            # Add member
            member_row = post_request("shared-budget-members/", {
                'shared-budget': budget_id,
                'user_id': user.id,
                'role': invite_row["role"],
                'contribution_percentage': 0, # Will be updated if equal split
            })

            # If equal split, update all members' contribution percentages
            if budget_row and budget_row["default_split_type"] == 'equal':
                member_rows = get_request("shared-budget-members/", shared_budget=budget_id) or []
                member_count = len(member_rows)
                percentage = 100.0 / member_count if member_count > 0 else 0

                for member in member_rows:
                    patch_request(f"shared-budget=members/{member['id']}", {
                        'contribution_percentage': percentage
                    })

            # Notify members
            budget_name = budget_row["name"] if budget_row else "Unknown Budget"
            member_rows = get_request("shared-budget-members/", shared_budget=budget_id) or []
            member_user_ids = [m["user_id"] for m in member_rows if m["user_id"] != user.id]

            for member_user_id in member_user_ids:
                post_request("shared-budget-notifications/", {
                    'user_id': member_user_id,
                    'from_user_id': user.id,
                    'notification_type': 'invite_accepted',
                    'shared_budget_id': budget_id,
                    'message': f'{user.username} joined budget "{budget_name}"'
                })

            budget_data = get_budget_data(budget_row, user.id) if budget_row else {}

            return JsonResponse({
                'message': f'You have joined "{budget_name}"',
                'budget': budget_data,
            })
        else:
            # Decline the invite via API
            updated_invite_row = patch_request(f"shared-budget-invites/{invite_id}", {'status': 'declined'})
            if not updated_invite_row:
                return JsonResponse({'error': 'Failed to decline invitation'}, status=500)

            # Notify the inviter
            inviter_row = get_request(f"users/{invite_row['invited_by']}")
            inviter_username = inviter_row["username"] if inviter_row else f"user_{invite_row['invited_by']}"

            post_request("shared-budget-notifications/", {
                'user_id': invite_row["invited_by"],
                'from_user_id': user.id,
                'notification_type': 'invite_declined',
                'shared_budget_id': invite_row["shared_budget"],
                'message': f'{user.username} declined your invitation to "{invite_row["shared_budget_name"]}"'
            })

            return JsonResponse({
                'message': 'Invitation declined'
            })
    except Exception as e:
        print(f"Error responding to budget invite: {e}")
        return JsonResponse({'error': 'Failed to process invitation response'}, status=500)

    
# ======================== MEMBER MANAGEMENT ===============================

@csrf_exempt
@login_required_json
def update_member_role(request, budget_id, member_id):
    """Update a member's role in a shared budget."""
    if request.method not in ['PUT', 'PATCH']:
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    user = request.user

    try:
        # Verify budget exists
        budget_row = get_request(f"shared-budgets/{budget_id}")
        if not budget_row:
            return JsonResponse({'error': 'Shared budget not found'}, status=404)

        # Only owner can change roles
        member_row = get_request("shared-budget-members/", shared_budget=budget_id, user_id=user.id)
        if not member_row or member_row["role"] != 'owner':
            return JsonResponse({'error': 'Only the owner can change member roles'}, status=403)

        # Verify member exists and belongs to this budget
        target_member_row = get_request(f"shared-budget-members/{member_id}")
        if not target_member_row or target_member_row["shared_budget"] != budget_id:
            return JsonResponse({'error': 'Member not found'}, status=404)

        # Can't change own role
        if target_member_row["user_id"] == user.id:
            return JsonResponse({'error': 'You cannot change your own role'}, status=400)

        new_role = data.get('role')
        if new_role not in ['editor', 'viewer']:
            return JsonResponse({'error': 'Invalid role. Use "editor" or "viewer"'}, status=400)

        # Update member role via API
        updated_member_row = patch_request(f"shared-budget-members/{member_id}", {'role': new_role})
        if not updated_member_row:
            return JsonResponse({'error': 'Failed to update member role'}, status=500)

        # If role changed to owner, we might need to handle ownership transfer logic
        # For now, just update the role

        member_data = get_member_data(updated_member_row, budget_row)

        return JsonResponse({
            'message': f'Update {member_data["user"]["username"]} role to {new_role}',
            'member': member_data,
        })
    except Exception as e:
        print(f"Error updating member role: {e}")
        return JsonResponse({'error': 'Failed to update member role'}, status=500)


@csrf_exempt
@login_required_json
def leave_budget(request, budget_id):
    """Leave a shared budget."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    user = request.user

    try:
        # Verify budget exists
        budget_row = get_request(f"shared-budgets/{budget_id}")
        if not budget_row:
            return JsonResponse({'error': 'Shared budget not found'}, status=404)

        # Verify user is a member
        member_row = get_request("shared-budget-members/", shared_budget=budget_id, user_id=user.id)
        if not member_row:
            return JsonResponse({'error': 'You are not a member of this budget'}, status=404)

        # Owner can't leave, must transfer or delete
        if member_row["role"] == 'owner':
            # Check if there are other members
            member_rows = get_request("shared-budget-members/", shared_budget=budget_id) or []
            other_members = [m for m in member_rows if m["user_id"] != user.id]

            if other_members:
                return JsonResponse({
                    'error': 'Owner cannot leave. Transfer ownership first or delete the budget.'
                }, status=400)
            else:
                # Last member, delete the budget
                budget_name = budget_row["name"]
                result = delete_request(f"shared-budgets/{budget_id}")
                if result is None:
                    return JsonResponse({'error': 'Failed to delete budget'}, status=500)

                return JsonResponse({'message': 'Budget deleted (you were the last member)'})

        # Notify members
        budget_name = budget_row["name"]
        member_rows = get_request("shared-budget-members/", shared_budget=budget_id) or []
        member_user_ids = [m["user_id"] for m in member_rows if m["user_id"] != user.id]

        for member_user_id in member_user_ids:
            post_request("shared-budget-notifications/", {
                'user_id': member_user_id,
                'from_user_id': user.id,
                'notification_type': 'member_left',
                'shared_budget_id': budget_id,
                'message': f'{user.username} left budget "{budget_name}"'
            })

        # Remove member via API
        result = delete_request(f"shared-budget-members/{member_row['id']}")
        if result is None:
            return JsonResponse({'error': 'Failed to leave budget'}, status=500)

        # Recalculate percentages for equal split
        if budget_row and budget_row["default_split_type"] == 'equal':
            member_row = get_request("shared-budget-members/", shared_budget=budget_id) or []
            if len(member_rows) > 0:
                percentage = 100.0 / len(member_rows)
                for member in member_rows:
                    patch_request(f"shared-budget-members/{member['id']}", {
                        'contribution_percentage': percentage
                    })

        return JsonResponse({
            'message': f'You have left "{budget_name}"'
        })
    except Exception as e:
        print(f"Error leaving budget: {e}")
        return JsonResponse({'error': 'Failed to leave budget'}, status=500)


@csrf_exempt
@login_required_json
def remove_member(request, budget_id, member_id):
    """Remove a member from a shared budget."""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    user = request.user

    try:
        # Verify budget exists
        budget_row = get_request(f"shared-budgets/{budget_id}")
        if not budget_row:
            return JsonResponse({'error': 'Shared budget not found'}, status=404)

        # Only owner can remove members
        member_row = get_request("shared-budget-members/", shared_budget=budget_id, user_id=user.id)
        if not member_row or member_row["role"] != 'owner':
            return JsonResponse({'error': 'Only the owner can remove members'}, status=403)

        # Verify member exists and belongs to this budget
        target_member_row = get_request(f"shared-budget-members/{member_id}")
        if not target_member_row or target_member_row["shared_budget"] != budget_id:
            return JsonResponse({'error': 'Member not found'}, status=404)

        # Can't remove yourself
        if target_member_row["user_id"] == user.id:
            return JsonResponse({'error': 'You cannot remove yourself. Use leave instead.'}, status=400)

        removed_username = get_username(target_member_row["user_id"])

        # Notify the removed member
        post_request("shared-budget-notifications/", {
            'user_id': target_member_row["user_id"],
            'from_user_id': user.id,
            'notification_type': 'member_left',
            'shared_budget_id': budget_id,
            'message': f'You were removed from budget "{budget_row["name"]}"'
        })

        # Remove member via API
        result = delete_request(f"shared-budget-members/{member_id}")
        if result is None:
            return JsonResponse({'error': 'Failed to remove member from budget'}, status=500)

        # Recalculate percentages for equal split
        if budget_row and budget_row["default_split_type"] == 'equal':
            member_rows = get_request("shared-budget-members/", shared_budget=budget_id) or []
            if len(member_rows) > 0:
                percentage = 100.0 / len(member_rows)
                for member in member_rows:
                    patch_request(f"shared-budget-members/{member['id']}", {
                        'contribution_percentage': percentage
                    })

        return JsonResponse({
            'message': f'Removed {removed_username} from budget'
        })
    except Exception as e:
        print(f"Error removing member: {e}")
        return JsonResponse({'error': 'Failed to remove member'}, status=500)


# ======================== EXPENSE MANAGEMENT =============================

@csrf_exempt
@login_required_json
def add_expense(request, budget_id):
    """Add an expense to a shared budget."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Shared budget not found'}, status=404)
    
    user = request.user

    try:
        # Verify budget exists
        budget_row = get_request(f"shared-budgets/{budget_id}")
        if not budget_row:
            return JsonResponse({'error': 'Shared budget not found'}, status=404)

        # Check permissions
        member_row = get_request("shared-budget-members/", shared_budget=budget_id, user_id=user.id)
        if not member_row or member_row["role"] not in ['owner', 'editor']:
            return JsonResponse({'error': 'You do not have permission to add expenses'}, status=403)

        # Validate fields
        if not data.get('description'):
            return JsonResponse({'error': 'Description is required'}, status=400)

        if not data.get('amount'):
            return JsonResponse({'error': 'Amount is required'}, status=400)

        try:
            amount = float(str(data['amount']))
            if amount <= 0:
                return JsonResponse({'error': 'Amount must be positive'}, status=400)
        except Exception:
            return JsonResponse({'error': 'Invalid amount'}, status=400)

        # Determine who paid
        paid_by_id = data.get('paid_by_id', user.id)

        # Verify payer exists
        paid_by_row = get_request(f"users/{paid_by_id}")
        if not paid_by_row:
            return JsonResponse({'error': 'Paid by user not found'}, status=404)

        # Verify payer is a member
        payer_member_row = get_request("shared-budget-members/", shared_budget=budget_id, user_id=paid_by_id)
        if not payer_member_row:
            return JsonResponse({'error': 'Payer must be a member of this budget'}, status=403)

        # Create expense via API
        expense_row = post_request("shared-expenses/", {
            'shared_budget': budget_id,
            'description': data['description'],
            'amount': str(amount),
            'paid_by': paid_by_id,
            'date': data.get('date', timezone.now().date().isoformat()),
            'category': data.get('category', ''),
            'created_by': user.id,
            'notes': data.get('notes', '')
        })

        if not expense_row:
            return JsonResponse({'error': 'Failed to create expense'}, status=500)

        # Create splits based on type
        split_type = data.get('split_type', budget_row["default_split_type"])
        splits_data = data.get('splits')

        if split_type == 'custom' and splits_data:
            # Custom splits provided via API
            for split_data in splits_data:
                post_request("expense-splits/", {
                    'shared_expense': expense_row["id"],
                    'user_id':split_data["user_id"],
                    'amount_owed': str(split_data["amount_owed"]),
                    'is_settled':split_data.get("is_settled", False)
                })
        else:
            # Default: equal split via API endpoint
            post_request(f"shared-expenses/{expense_row['id']}/create-equal-splits", {})

        # Notify members
        expense_description = data['description']
        member_rows = get_request("shared-budget-members/", shared_budget=budget_id) or []
        member_user_ids = [m["user_id"] for m in member_rows if m["user_id"] != user.id]

        for member_user_id in member_user_ids:
            post_request("shared-budget-notifications/", {
                'user_id': member_user_id,
                'from_user_id': user.id,
                'notification_type': budget_id,
                'message': f'{user.username} added "{expense_description}" (${amount}) to "{budget_row["name"]}"'
            })

        expense_data = get_expense_data(expense_row)

        return JsonResponse({
            'message': 'Expense added susccesfully',
            'expense': expense_data,
        }, status=201)
    except Exception as e:
        print(f"Error adding expense: {e}")
        return JsonResponse({'error': 'Failed to add expense'}, status=500)


@csrf_exempt
@login_required_json
def update_expense(request, budget_id, expense_id):
    """Update an expense in a shared budget."""
    if request.method not in ['PUT', 'PATCH']:
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    user = request.user

    try:
        # Verify budget exists
        budget_row = get_request(f"shared-budgets/{budget_id}")
        if not budget_row:
            return JsonResponse({'error': 'Shared budget not found'}, status=404)

        # Check permissions
        member_row = get_request("shared-budget-members/", shared_budget=budget_id, user_id=user.id)
        if not member_row or member_row["role"] not in ['owner', 'editor']:
            return JsonResponse({'error': 'You do not have permission to edit expenses'}, status=403)

        # Verify expense exists and belongs to this budget
        expense_row = get_request(f"shared-expenses/{expense_id}")
        if not expense_row or expense_row["shared_budget"] != budget_id:
            return JsonResponse({'error': 'Expense not found'}, status=404)

        # Update fields
        payload = {}
        if 'description' in data:
            payload['description'] = data['description']
        if 'amount' in data:
            try:
                payload['amount'] = str(float(data['amount']))
            except Exception:
                return JsonResponse({'error': 'Invalid amount'}, status=400)
        if 'date' in data:
            payload['date'] = data['date']
        if 'category' in data:
            payload['category'] = data['category']
        if 'notes' in data:
            payload['notes'] = data['notes']

        if not payload:
            return JsonResponse({'error': 'No valid fields to update'}, status=400)

        # Update expense via API
        updated_expense_row = patch_request(f"shared-expenses/{expense_id}", payload)
        if not updated_expense_row:
            return JsonResponse({'error': 'Failed to update expense'}, status=500)

        # Recalculate splits if amount changed
        if 'amount' in data:
            # Delete existing splits via API
            split_rows = get_request("expense=splits/", shared_expense=expense_id) or []
            for split_row in split_rows:
                delete_request(f"expense-splits/{split_row['id']}")

            # Create new splits based on type
            split_type = data.get('split_type', budget_row["default_split_type"])

            if split_type == 'custom' and data.get('splits'):
                # Custom splits provided
                for split_data in data['splits']:
                    post_request("expense-splits/", {
                        'shared_expense': expense_id,
                        'user_id': split_data["user_id"],
                        'amount_owed': str(split_data["amount_owed"]),
                        'is_settled': split_data.get("is_settled", False),
                    })
            elif split_type == 'percentage':
                # Percentage splits
                post_request(f"shared-expenses/{expense_id}/create-percentage-splits", {})
            else:
                # Equal splits
                post_request(f"shared-expenses/{expense_id}/create-equal-splits", {})

        # Notify members
        member_rows = get_request("shared-budget-members/", shared_budget=budget_id) or []
        member_user_ids = [m["user_id"] for m in member_rows if m["user_id"] != user.id]

        for member_user_id in member_user_ids:
            post_request("shared-budget-notifications/", {
                'user_id': member_user_id,
                'from_user_id': user.id,
                'notification_type': 'expense_updated',
                'shared_budget_id': budget_id,
                'message': f'{user.username} updated "{expense_row["description"]}" in "{budget_row["name"]}"'
            })

        expense_data = get_expense_data(updated_expense_row)

        return JsonResponse({
            'message': 'Expense updated successfully',
            'expense': expense_data,
        })
    except Exception as e:
        print(f"Error updating expense: {e}")
        return JsonResponse({'error': 'Failed to update expense'}, status=500)


@csrf_exempt
@login_required_json
def delete_expense(request, budget_id, expense_id):
    """Delete an expense from a shared budget."""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    user = request.user

    try:
        # Verify budget exists
        budget_row = get_request(f"shared-bugdets/{budget_id}")
        if not budget_row:
            return JsonResponse({'error': 'Shared budget not found'}, status=404)

        # Check permissions
        member_row = get_request("shared-budget-members/", shared_budget=budget_id, user_id=user.id)
        if not member_row or member_row["role"] not in ['owner', 'editor']:
            return JsonResponse({'error': 'You do not have permission to delete expenses'}, status=403)

        # Verify expense exists and belongs to this budget
        expense_row = get_request(f"shared-expenses/{expense_id}")
        if not expense_row or expense_row["shared_budget"] != budget_id:
            return JsonResponse({'error': 'Expense not found'}, status=404)

        description = expense_row["description"]

        # Notify members
        member_rows = get_request("shared-budget-members/", shared_budget=budget_id) or []
        member_user_ids = [m["user_id"] for m in member_rows if m["user_id"] != user.id]

        for member_user_id in member_user_ids:
            post_request("shared-budget-notifications/", {
                'user_id': member_user_id,
                'from_user_id': user.id,
                'notification_type': 'expense_deleted',
                'shared_budget_id': budget_id,
                'message': f'{user.username} deleted "{description}" from "{budget_row["name"]}"'
            })

        # Delete expense via API
        result = delete_request(f"shared-expenses/{expense_id}")
        if result is None:
            return JsonResponse({'error': 'Failed to delete expense'}, status=500)

        return JsonResponse({
            'message': f'Expense "{description}" deleted succesfully'
        })
    except Exception as e:
        print(f"Error deleting expense: {e}")
        return JsonResponse({'error': 'Failed to delete expense'}, status=500)


@csrf_exempt
@login_required_json
def get_budget_expenses(request, budget_id):
    """Get all expenses for a shared budget."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    user = request.user

    try:
        # Verify budget exists
        budget_row = get_request(f"shared-budgets/{budget_id}")
        if not budget_row:
            return JsonResponse({'error': 'Shared budget not found'}, status=404)

        # Verify user is a member
        member_row = get_request("shared-budget-members/", shared_budget=budget_id, user_id=user.id)
        if not member_row:
            return JsonResponse({'error': 'You are not a member of this budget'}, status=404)

        # Get expenses
        expense_rows = get_request("shared-expenses/", shared_budget=budget_id) or []

        # Optional filters
        category = request.GET.get('category')
        if category:
            expense_rows = [e for e in expense_rows if e.get("category") == category]

        paid_by = request.GET.get('paid_by')
        if paid_by:
            try:
                paid_by_id = int(paid_by)
                expense_rows = [e for e in expense_rows if e.get("paid_by") == paid_by_id]
            except ValueError:
                pass # Invalid paid_by parameter, ignore filter

        expenses_data = [get_expense_data(expense_row) for expense_row in expense_rows]

        # Calculate total
        total = sum(expense["amount"] for expense in expenses_data)

        return JsonResponse({
            'expenses': expenses_data,
            'total': total,
            'count': len(expenses_data),
        })
    except Exception as e:
        print(f"Error getting budget expenses: {e}")
        return JsonResponse({'error': 'Failed to get budget expenses'}, status=500)


# ========================== SETTLEMENTS ===============================

@csrf_exempt
@login_required_json
def create_settlement(request, budget_id):
    """Create a settlement (payment between users)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    user = request.user

    try:
        # Verify budget exists
        budget_row = get_request(f"shared-budgets/{budget_id}")
        if not budget_row:
            return JsonResponse({'error': 'Shared budget not found'}, status=404)

        if not budget_row["is_active"]:
            return JsonResponse({'error': 'Budget is not active'}, status=400)

        # Check if user is a member
        member_row = get_request("shared-budget-members/", shared_budget=budget_id, user_id=user.id)
        if not member_row:
            return JsonResponse({'error': 'You are not a member of this budget'}, status=403)

        receiver_id = data.get('receiver_id')
        if not receiver_id:
            return JsonResponse({'error': 'receiver_id is required'}, status=400)

        # Verify receiver exists
        receiver_row = get_request(f"users/{receiver_id}")
        if not receiver_row:
            return JsonResponse({'error': 'Receiver not found'}, status=404)

        # Verify receiver is a member
        receiver_member_row = get_request("shared-budget-members/", shared_budget=budget_id, user_id=receiver_id)
        if not receiver_member_row:
            return JsonResponse({'error': 'Receiver must be a member of this budget'}, status=403)

        if receiver_id == user.id:
            return JsonResponse({'error': 'You cannot settle with yourself'}, status=400)

        try:
            amount = float(str(data.get('amount', 0)))
            if amount <= 0:
                return JsonResponse({'error': 'Amount must be positive'}, status=400)
        except Exception:
            return JsonResponse({'error': 'Invalid amount'}, status=400)

        # Create settlement via API
        settlement_row = post_request("settlements/", {
            'shared_budget': budget_id,
            'payer': user.id,
            'receiver': receiver_id,
            'amount': str(amount),
            'date': data.get('date', timezone.now().date().isoformat()),
            'notes': data.get('notes', '')
        })

        if not settlement_row:
            return JsonResponse({'error': 'Failed to create settlement'}, status=500)

        # Notify receiver
        post_request("shared-budget-notifications/", {
            'user_id': receiver_id,
            'from_user_id': user.id,
            'notification_type': 'settlement_made',
            'shared_budget_id': budget_id,
            'message': f'{user.username} paid you ${amount} for "{budget_row["name"]}"'
        })

        settlement_data = {
            'id': settlement_row["id"],
            'payer': {
                'id': user.id,
                'username': user.username,
            },
            'receiver': {
                'id': receiver_id,
                'username': receiver_row["username"],
            },
            'amount': float(amount),
            'date': settlement_row.get("date"),
            'notes': settlement_row.get("notes", ""),
            'created_at': settlement_row.get("created_at"),
        }

        return JsonResponse({
            'message': f'Settlement of ${amount} recorded',
            'settlement': settlement_data,
        }, status=201)
    except Exception as e:
        print(f"Error creating settlement: {e}")
        return JsonResponse({'error': 'Failed to create settlement'}, status=500)


@csrf_exempt
@login_required_json
def get_budget_debts(request, budget_id):
    """Get all debts/balances for a shared budget."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    user = request.user

    try:
        # Verify budget exists
        budget_row = get_request(f"shared-budgets/{budget_id}")
        if not budget_row:
            return JsonResponse({'error': 'Shared budget not found'}, status=404)

        # Check if user is a member
        member_row = get_request("shared-budget-members/", shared_budget=budget_id, user_id=user.id)
        if not member_row:
            return JsonResponse({'error': 'You are not a member of this budget'}, status=403)

        # Get debts data
        debts_data = get_budget_debts_data(budget_id)

        # Get user-specific debts
        user_owes = [d for d in debts_data if d['from_user']['id'] == user.id]
        user_owed = [d for d in debts_data if d['to_user']['id'] == user.id]

        is_settled = len(debts_data) == 0

        return JsonResponse({
            'all_debts': debts_data,
            'you_owe': user_owes,
            'you_are_owed': user_owed,
            'is_settled': is_settled,
        })
    except Exception as e:
        print(f"Error getting budget debts: {e}")
        return JsonResponse({'error': 'Failed to get budget debts'}, status=500)


# ================================= NOTIFICATIONS =====================================

@csrf_exempt
@login_required_json
def get_budget_notifications(request):
    """Get shared budget notifications for the logged-in user."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    user = request.user
    unread_only = request.GET.get('unread_only', 'false').lower() == 'true'

    try:
        # Get notifications
        notification_rows = get_request("shared-budget-notifications/", user_id=user.id) or []

        if unread_only:
            notification_rows = [n for n in notification_rows if not n.get("is_read", False)]

        # Sort by date descending and limit to 50
        notification_rows.sort(ket=lambda x: x.get("created_at") or "", reverse=True)
        notification_rows = notification_rows[:50]

        notifications_data = []
        for notification_row in notification_rows:
            budget_row = None
            if notification_row.get("shared_budget"):
                budget_row = get_request(f"shared-budgets/{notification_row['shared_budget']}")

            from_user_row = get_request(f"users/{notification_row['from_user']}")

            notifications_data.append({
                'id': notification_row["id"],
                'type': notification_row["notification_type"],
                'message': notification_row["message"],
                'from_user': {
                    'id': notification_row["from_user"],
                    'username': from_user_row["username"] if from_user_row else f"user_{notification_row['from_user']}", 
                },
                'budget': {
                    'id': notification_row["shared_budget"],
                    'name': budget_row["name"] if budget_row else "Unknown Budget",
                } if notification_row.get("shared_budget") else None,
                'is_read': notification_row.get("created_at"),
            })

        unread_count = len([n for n in notification_rows if not n.get("is_read", False)])

        return JsonResponse({
            'notifications': notifications_data,
            'unread_count': unread_count,
        })
    except Exception as e:
        print(f"Error getting budget notifications: {e}")
        return JsonResponse({'error': 'Failed to get budget notifications'}, status=500)


# ========================= HELPER FUNCTIONS FOR EXPENSES ===================================

def get_expense_data(expense_row):
    """Get expense data from API row."""
    # Get splits for this expense
    split_rows = get_request("expense-splits/", shared_expense=expense_row["id"]) or []
    splits_data = []
    for split_row in split_rows:
        user_row = get_request(f"users/{split_row['user_id']}")
        splits_data.append({
            'id': split_row["id"],
            'user': {
                'id': split_row["id"],
                'username': user_row["username"] if user_row else f"user_{split_row['user_id']}",
            },
            'amount_owed': float(split_row["amount_owed"]),
            'is_settled': split_row["is_settled"],
            'settled_at': split_row.get("settled_at"),
        })

    # Get payer info
    payer_row = get_request(f"users/{expense_row['paid_by']}")

    # Get creator info
    creator_row = get_request(f"users/{expense_row['created_by']}")

    return {
        'id': expense_row["id"],
        'description': expense_row["description"],
        'amount': float(expense_row["amount"]),
        'paid_by': {
            'id': expense_row["paid_by"],
            'username': payer_row["username"] if payer_row else f"user_{expense_row['paid_by']}",
            'first_name': payer_row["first_name"] if payer_row else "",
            'last_name':payer_row["last_name"] if payer_row else "",
        },
        'created_by': {
            'id': expense_row["created_by"],
            'username': creator_row["username"] if creator_row else f"user_{expense_row['created_by']}",
        },
        'date': expense_row.get("date"),
        'category': expense_row.get("category", ""),
        'notes': expense_row.get("notes", ""),
        'created_at': expense_row.get("created_at"),
        'splits': splits_data,
    }


def get_budget_debts_data(budget_id):
    """Get all debts/balances for a shared budget from API."""
    try:
        # Try to get debts from API endpoint first
        debts_rows = get_request(f"shared-budgets/{budget_id}/debts") or []
        if debts_rows:
            debts_data = []
            for debt_row in debts_rows:
                debts_data.append({
                    'from_user': {
                        'id': debt_row["from_user_id"],
                        'username': get_username(debt_row["from_user_id"]),
                    },
                    'to_user': {
                        'id': debt_row["to_user_id"],
                        'username': get_username(debt_row["to_user_id"]),
                    },
                    'amount': float(debt_row["amount"]),
                })
            return debts_data
    except Exception:
        pass # Fall back to calculation if API ednpoint doesn't exist

    # Calculate debts manually (similar to original calulate_debts function)
    members = get_request("shared-budget-members/", shared_budget=budget_id) or []
    balances = {}

    for member_row in members:
        user_id = member_row["user_id"]

        # Total paid by this member
        expense_rows = get_request("shared-expenses/", shared_budget=budget_id, paid_by=user_id) or []
        total_paid = sum(float(expense_row["amount"]) for expense_row in expense_rows)

        # Total owed by this member (from splits)
        split_rows = get_request("expense-splits/", shared_budget=budget_id, user_id=user_id, is_settled=False) or []
        total_owed = sum(float(split_row["amount_owed"]) for split_row in split_rows)

        # Total settlements made by this member
        settlement_rows = get_request("settlements/", shared_budget=budget_id, payer=user_id) or []
        settlements_paid = sum(float(settlement_row["amount"]) for settlement_row in settlement_rows)

        # Total settlements received by this member
        settlement_rows = get_request("settlements/", shared_budget=budget_id, receiver=user_id) or []
        settlements_received = sum(float(settlement_row["amount"]) for settlement_row in settlement_rows)

        # Net balance: positive means others owe them
        balance = total_paid - total_owed - settlements_received + settlements_paid
        balances[user_id] = {
            'user': user_id,
            'balance': balance
        }

    # Calculate simplified debts
    debtors = [] # People who owe (negative balance)
    creditors = [] # People who are owed (positive balance)

    for user_id, data in balances.items():
        if data['balance'] < 0:
            debtors.append({
                'user': get_user_data(user_id),
                'amount': abs(data['balance'])
            })
        elif data['balance'] > 0:
            creditors.append({
                'user': get_user_data(user_id),
                'amount': data['balance']
            })

    # Sort for optimal settlement
    debtors.sort(key=lambda x: x.get['amount'], reverse=True)
    creditors.sort(key=lambda x: x.get['amout'], reverse=True)

    debts = []
    i, j = 0, 0

    while i < len(debtors) and j < len(creditors):
        debtor = debtors[i]
        creditor = creditors[j]

        settle_amount = min(debtor['amount'], creditor['amount'])

        if settle_amount > 0.01:
            debts.append({
                'from_user': debtor['user'],
                'to_user': creditor['user'],
                'amount': float(settle_amount)
            })

        debtor['amount'] -= settle_amount
        creditor['amount'] -= settle_amount

        if debtor['amount'] <= 0.01:
            i += 1
        if creditor['amount'] <= 0.01:
            j += 1

    return debts
