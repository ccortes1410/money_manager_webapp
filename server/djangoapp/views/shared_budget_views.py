from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.db.models import Q, Sum
from django.utils import timezone
from functools import wraps
import json

from ..models.models import (
    SharedBudget,
    SharedBudgetMember,
    SharedBudgetInvite,
    SharedExpense,
    ExpenseSplit,
    Settlement,
    SharedBudgetNotification,
)
from ..models.friendship import Friendship


def login_required_json(view_func):
    """Decorator to check if user is authenticated."""
    @wraps(view_func)
    def wrapper (request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper


# ===================== HELPER FUNCTIONS ===================

def serialize_member(member, budget=None):
    """Serialize a SharedBudgetMember to dict."""
    budget = budget or member.shared_budget

    total_paid = float(member.get_total_paid())
    total_owed = float(member.get_total_owed())
    balance = total_paid - total_owed

    return {
        'id': member.id,
        'user': {
            'id': member.user.id,
            'username': member.user.username,
            'email': member.user.email,
            'first_name': member.user.first_name,
            'last_name': member.user.last_name,
        },
        'role': member.role,
        'contribution_percentage': float(member.contribution_percentage),
        'joined_at': member.joined_at.isoformat(),
        'total_paid': total_paid,
        'total_owed': total_owed,
        'balance': balance,
    }


def serialize_expense(expense):
    splits = expense.splits.all()

    return {
        'id': expense.id,
        'desription': expense.description,
        'amount': float(expense.amount),
        'paid_by': {
            'id': expense.paid_by.id,
            'username': expense.paid_by.username,
            'first_name': expense.paid_by.first_name,
            'last_name': expense.paid_by.last_name,
        },
        'created_by': {
            'id': expense.created_by.id,
            'username': expense.created_by.username,
        },
        'date': expense.date.isoformat(),
        'category': expense.category,
        'notes': expense.notes,
        'created_at': expense.created_at.isoformat(),
        'splits': [{
            'id': split.id,
            'user': {
                'id': split.user.id,
                'username': split.user.username,
            },
            'amount_owed': float(split.amount_owed),
            'is_settled': split.is_settled,
            'settled_at': split.settle_at.isoformat() if split.settled_at else None,
        } for split in splits],
    }


def serialize_budget(budget, user=None):
    """Serialize a SharedBudget to dict."""
    total_spent = float(budget.get_total_spent())
    total_amount = float(budget.total_amount)
    remaining = total_amount - total_spent
    progress = budget.get_progress_percentage()

    members = budget.members.all()
    members_data = [serialize_member(m, budget) for m in members]

    # Get current user's role and balance
    user_role = None
    user_balanace = 0
    if user:
        member = members.filter(user=user).first()
        if member:
            user_role = member.role
            user_balanace = float(member.get_balance())

    return {
        'id': budget.id,
        'name': budget.name,
        'description': budget.description,
        'total_amount': total_amount,
        'total_spent': total_spent,
        'remaining': remaining,
        'progress': progress,
        'category': budget.category,
        'created_by': {
            'id': budget.created_by.id,
            'username': budget.created_by.username,
        },
        'start_date': budget.start_date.isoformat(),
        'end_date': budget.end_date.isoformat(),
        'is_active': budget.is_active,
        'default_split_type': budget.default_split_type,
        'member_count': members.count(),
        'members': members_data,
        'user_role': user_role,
        'user_balance': user_balanace,
        'created_at': budget.created_at.isoformat(),
    }


def notify_budget_members(budget, from_user, notification_type, message, exclude_user=None):
    """Send notification to all budget members except the sender."""
    members = budget.members.all()
    
    for member in members:
        if member.user == from_user:
            continue
        if exclude_user and member.user == exclude_user:
            continue

        SharedBudgetNotification.objects.create(
            user=member.user,
            from_user=from_user,
            notification_type=notification_type,
            shared_budget=budget,
            message=message
        )


def calculate_debts(budget):
    """
    Calculate who owes whom in a share budget.
    Returns list of {'from': user, 'to': user, 'amount': decimal}
    """

    members = budget.members.all()
    balances = {}

    for member in members:
        # Total paid by this members
        total_paid = SharedExpense.objects.filter(
            shared_budget=budget,
            paid_by=member.user
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Total owed by this member (from splits)
        total_owed = ExpenseSplit.objects.filter(
            expense__shared_budget=budget,
            user=member.user,
            is_settled=False
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Total settlementsmade by this member
        settlements_paid = Settlement.objects.filter(
            shared_budget=budget,
            payer=member.user
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Total settlements received by this member
        settlements_received = Settlement.objects.filter(
            shared_budget=budget,
            receiver=member.user
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Net balance: positive means others owe them
        balance = total_paid - total_owed - settlements_received + settlements_paid
        balances[member.user.id] = {
            'user': member.user,
            'balance': balance
        }
    
    # Calculate simplified debts
    debtors = [] # People who owe (negative balance)
    creditors = [] # People who are owed (positive balance)

    for user_id, data in balances.items():
        if data['balance'] < 0:
            debtors.append({'user': data['user'], 'amount': abs(data['balance'])})
        elif data['balance'] > 0:
            creditors.append({'user': data['user'], 'amount': data['balance']})

    # Sort for optimal settlement
    debtors.sort(key=lambda x: x['amount'], revers=True)
    creditors.sort(key=lambda x: x['amount'], reverse=True)

    debts = []
    i, j = 0, 0

    while i < len(debtors) and j < len(creditors):
        debtor = debtor[i]
        creditor = creditor[j]

        settle_amount =min(debtor['amount'], creditor['amount'])

        if settle_amount > float(0.01):
            debts.append({
                'from_user': {
                    'id': debtor['user'].id,
                    'username': debtor['user'].username,
                    'first_name': debtor['user'].first_name,
                    'last_name': debtor['user'].last_name,
                },
                'to_user': {
                    'id': creditor['user'].id,
                    'username': creditor['user'].username,
                    'first_name': creditor['user'].first_name,
                    'last_name': creditor['user'].last_name,
                },
                'amount': float(settle_amount)
            })
        
        debtor['amount'] -= settle_amount
        creditor['amount'] -= settle_amount

        if debtor['amount'] <= float(0.01):
            i += 1
        if creditor['amount'] <= float(0.01):
            j += 1

    return debts

# ============================= SHARED BUDGET CRUD ==========================

@csrf_exempt
@login_required_json
def get_shared_budgets(request):
    """Get all shared budgets the user is a member of."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    user = request.user

    # Get budgets where user is a member
    memberships = SharedBudgetMember.objects.filter(user=user)
    budgets = [m.shared_budget for m in memberships]

    # Separate active and inactive
    active_budgets = [b for b in budgets if b.is_active]
    inactive_budgets = [b for b in budgets if not b.is_active]

    # Get pending invites
    pending_invites = SharedBudgetInvite.objects.filter(
        invited_user=user,
        status='pending'
    )

    invites_data = [{
        'id': invite.id,
        'budget_name': invite.shared_budget.name,
        'buget_amount': float(invite.shared_budget.total_amount),
        'invited_by': {
            'id': invite.invited_by.id,
            'username': invite.invited_by.username,
            'first_name': invite.invited_by.first_name,
            'last_name': invite.invited_by.last_name,
        },
        'role': invite.role,
        'message': invite.message,
        'created_at': invite.create_at.isoformat(),
    } for invite in pending_invites]

    return JsonResponse({
        'active_budgets': [serialize_budget(b, user) for b in active_budgets],
        'inactive_budgets': [serialize_budget(b, user) for b in inactive_budgets],
        'pending_invites': invites_data,
        'total_count': len(budgets),
        'active_count': len(active_budgets),
        'inactive_count': len(inactive_budgets),
    })


@csrf_exempt
@login_required_json
def get_shared_budget_detail(request, budget_id):
    """Get detailed info for a specific shared budget."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    user = request.user

    try:
        budget = SharedBudget.objects.filter(id=budget_id)
    except SharedBudget.DoesNotExist:
        return JsonResponse({'error': 'Shared budget not found'}, status=404)
    
    # Check if user is a member
    if not budget.is_member(user):
        return JsonResponse({'error': 'You are not a member of this budget'}, status=403)
    
    # Get recent expenses
    expenses = budget.expenses.all()[:20]
    expenses_data = [serialize_expense(e) for e in expenses]

    # Get debts
    debts = calculate_debts(budget)

    # Get settlements
    settlements = Settlement.objects.filter(shared_budget=budget)[:10]
    settlements_data = [{
        'id': s.id,
        'payer': {
            'id': s.payer.id,
            'username': s.payer.username,
            'fist_name': s.payer.first_name,
            'last_name': s.payer.last_name,
        },
        'receiver': {
            'id': s.receiver.id,
            'username': s.receiver.username,
            'first_name': s.receiver.first_name,
            'last_name': s.recevier.last_name,
        },
        'amount': float(s.amount),
        'date': s.date.isoformat(),
        'notes': s.notes,
        'created_at': s.created_at.isoformat(),
    } for s in settlements]

    budget_data = serialize_budget(budget, user)
    budget_data['expenses'] = expenses_data
    budget_data['debts'] = debts
    budget_data['settlements'] = settlements_data

    return JsonResponse(budget_data)


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
    required_fields = ['name', 'total_amount', 'start_date', 'end_date']
    for field in required_fields:
        if not data.get(field):
            return JsonResponse({'error': f'{field} is required'}, status=400)
    
    try:
        total_amount = float(str(data['total_amount']))
        if total_amount <= 0:
            return JsonResponse({'error': 'Total amount must be positive'}, status=400)
    except Exception:
        return JsonResponse({'error': 'Invalid total amount'}, status=400)
    
    # Create the budget
    try:
        budget = SharedBudget.objects.create(
            name=data['name'],
            description=data.get('description',''),
            total_amount=total_amount,
            category=data.get('categpory',''),
            created_by=user,
            start_date=data['start_date'],
            end_date=data['end_date'],
            default_split_type=data.get('split_type', 'equal'),
        )
    except Exception as e:
        return JsonResponse({'error': f'Error creating budget: {str(e)}'}, status=500)
    
    # Ad creator as owner
    SharedBudgetMember.objects.create(
        shared_budget=budget,
        user=user,
        role='owner',
        contribution_percentage=float(100)
    )

    # Send invites to friends if provided
    invited_friends = data.get('invite_friends', [])
    invites_sent = 0

    for friend_data in invited_friends:
        friend_id = friend_data.get('user_id') if isinstance(friend_data, dict) else friend_data

        try:
            friend = User.objects.get(id=friend_id)
        except User.DoesNotExist:
            continue

        # Verify they are friends
        if not Friendship.are_friends(user, friend):
            continue

        # Create invite
        try:
            role = friend_data.get('role', 'editor') if isinstance(friend_data, dict) else 'editor'

            SharedBudgetInvite.objects.create(
                shared_budget=budget,
                invited_by=user,
                invited_user=friend,
                role=role,
                message=data.get('invite_message', f'{user.username} invited you to "{budget.name}"')
            )

            # Create notification
            SharedBudgetNotification.objects.create(
                user=friend,
                from_user=user,
                notification_type='budget_invite',
                shared_budget=budget,
                message=f'{user.username} invited you to shared budget "{budget.name}"'
            )

            invites_sent += 1
        except Exception:
            continue
    
    return JsonResponse({
        'message': 'Shared budget created succesfully',
        'budget': serialize_budget(budget, user),
        'invites_sent': invites_sent,
    }, status=201)


@csrf_exempt
@login_required_json
def update_shared_budget(request, budget_id):
    """Update a shared budget."""
    if request.method not in ['PUT', 'PATCH']:
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    try:
        data = json.load(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    user = request.user

    try:
        budget = SharedBudget.objects.filter(id=budget_id)
    except SharedBudget.DoesNotExist:
        return JsonResponse({'error': 'Shared budget not found'}, status=404)
    
    # Check permissions
    if not budget.can_edit(user):
        return JsonResponse({'error': 'You do not have permission to edit this budget'}, status=403)
    
    # Update fields
    if 'name' in data:
        budget.name = data['name']
    if 'description' in data:
        budget.description = data['description']
    if 'total_amount' in data:
        try:
            budget.total_amount = float(str(data['total_amount']))
        except Exception:
            return JsonResponse({'error': 'Invalid total amount'}, status=400)
    if 'category' in data:
        budget.category = data['category']
    if 'start_date' in data:
        budget.start_date = data['start_date']
    if 'end_date' in data:
        budget.end_date = data['end_date']
    if 'is_active' in data:
        budget.is_active = data['is-active']
    if 'split_type' in data:
        budget.default_split_type = data['split_type']
    
    budget.save()

    notify_budget_members(
        budget, user, 'budget_updated',
        f'{user.username} updated budget "{budget.name}"'
    )

    return JsonResponse({
        'message': 'Budget updated succesfully',
        'budget': serialize_budget(budget, user)
    })


@csrf_exempt
@login_required_json
def delete_shared_budget(request, budget_id):
    """Delete a shared budget."""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    user = request.user

    try:
        budget = SharedBudget.objects.filter(id=budget_id)
    except SharedBudget.DoesNotExist:
        return JsonResponse({'error': 'Shared budget not found'}, status=404)
    
    if not budget.can_delete(user):
        return JsonResponse({'error': 'Only the owner can delete this budget'}, status=403)
    
    budget_name = budget.name
    budget.delete()

    return JsonResponse({
        'message': f'Budget "{budget_name}" deleted succesfully'
    })

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
        budget = SharedBudget.objects.get(id=budget_id)
    except SharedBudget.DoesNotExist:
        return JsonResponse({'error': 'Shared budget not foun'}, status=404)
    
    # Check if user can invite (must be owner or editor)
    if not budget.can_edit(user):
        return JsonResponse({'error': 'You do not have permission to invite members'}, status=403)
    
    friend_id = data.get('user_id')
    if not friend_id:
        return JsonResponse({'error': 'user_id is required'}, status=400)
    
    try:
        friend = User.objects.get(id=friend_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
    # Verify they are friends
    if not Friendship.are_friends(user, friend):
        return JsonResponse({'error': 'You can only invite friends'}, status=400)
    
    # Check if already a member
    existing_invite = SharedBudgetInvite.objects.filter(
        shared_budget=budget,
        invited_user=friend,
        status='pending'
    ).first()

    if existing_invite:
        return JsonResponse({'error': 'An invite has already been sent to this user'}, status=400)
    
    # Create invite
    role = data.get('role', 'editor')
    message = data.get('message', f'{user.username} invited you to "{budget.name}"')

    invite = SharedBudgetInvite.objects.create(
        shared_budget=budget,
        invited_by=user,
        invited_user=friend,
        role=role,
        message=message
    )

    # Create notification
    SharedBudgetNotification.objects.create(
        user=friend,
        from_user=user,
        notification_type='budget_invite',
        shared_budget=budget,
        message=f'{user.username} invited you to shared budget "{budget.name}"'
    )

    return JsonResponse({
        'message': f'Invitation sent to {friend.username}',
        'invite': {
            'id': invite.id,
            'invited_user': {
                'id': friend.id,
                'username': friend.username,
            },
            'role': invite.role,
            'status': invite.status
        }
    }, status=201)


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
        invite = SharedBudgetInvite.objects.get(id=invite_id, invited_user=user, status='pending')
    except SharedBudgetInvite.DoesNotExist:
        return JsonResponse({'error': 'Invitation not found'}, status=404)
    
    if action == 'accept':
        invite.accept()

        # Update contribution percentages for equal split
        budget = invite.shared_budget
        if budget.default_split_type == 'equal':
            member_count = budget.members.count()
            percentage = float(100) / member_count
            budget.members.all().update(contribution_percentage=percentage)

        # Notify members
        notify_budget_members(
            budget, user, 'invite_accepted',
            f'{user.username} joined budget "{budget.name}"'
        )

        return JsonResponse({
            'message': f'You have joined "{invite.shared_budget.name}"',
            'budget': serialize_budget(invite.shared_budget, user)
        })
    
    else:
        invite.decline()

        # Notify the inviter
        SharedBudgetNotification.objects.create(
            user=invite.invited_by,
            from_user=user,
            notification_type='invite_declined',
            shared_budget=invite.shared_budget,
            message=f'{user.username} declined your invitation to "{invite.shared_budget.name}"'
        )

        return JsonResponse({
            'message': 'Invitation declined'
        })
    
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
        budget = SharedBudget.objects.get(id=budget_id)
    except SharedBudget.DoesNotExist:
        return JsonResponse({'error': 'Shared budget not found'}, status=404)
    
    # Only owner can change roles
    if not budget.can_delete(user):
        return JsonResponse({'error': 'Only the owner can change member roles'}, status=403)
    
    try:
        member = SharedBudgetMember.objects.get(id=member_id, shared_budget=budget)
    except SharedBudgetMember.DoesNotExist:
        return JsonResponse({'error': 'Member not found'}, status=404)
    
    # Can't change own role
    if member.user == user:
        return JsonResponse({'error': 'You cannot change your own role'}, status=400)
    
    new_role = data.get('role')
    if new_role not in ['editor', 'viewer']:
        return JsonResponse({'error': 'Invalid role. Use "editor" or "viewer"'}, status=400)
    
    member.role = new_role
    member.save()

    return JsonResponse({
        'message': f'Update {member.user.username} role to {new_role}',
        'member': serialize_member(member)
    })


@csrf_exempt
@login_required_json
def leave_budget(request, budget_id):
    """Leave a shared budget."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    user = request.user

    try:
        budget = SharedBudget.objects.get(id=budget_id)
    except SharedBudget.DoesNotExist:
        return JsonResponse({'error': 'Share budget not found'}, status=404)
    
    try:
        member = SharedBudgetMember.objects.get(shared_budget=budget, user=user)
    except SharedBudgetMember.DoesNotExist:
        return JsonResponse({'error': 'You are not a member of this budget'}, status=404)
    
    # Owner can't leave, must transfer or delete
    if member.role == 'owner':
        other_members = budget.members.exclude(user=user)
        if other_members.exists():
            return JsonResponse({
                'error': 'Owner cannot leave. Transfer ownership first or delete the budget.'
            }, status=400)
        else:
            # Last member, delete the budget
            budget.delete()
            return JsonResponse({'message': 'Budget deleted (you were the last member)'})
        
    # Notify members
    notify_budget_members(
        budget, user, 'member_left',
        f'{user.username} left budget "{budget.name}"'
    )

    member.delete()

    # Recalculate percentages for equal split
    if budget.default_split_type == 'equal':
        remaining_members = budget.members.count()
        if remaining_members > 0:
            percentage = float(100) / remaining_members
            budget.members.all().update(contribution_percentage=percentage)
    
    return JsonResponse({
        'message': f'You have left "{budget.name}"'
    })
    

@csrf_exempt
@login_required_json
def remove_member(request, budget_id, member_id):
    """Remove a member from a shared budget."""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    user = request.user

    try:
        budget = SharedBudget.objects.get(id=budget_id)
    except SharedBudget.DoesNotExist:
        return JsonResponse({'error': 'Shared budget not found'}, status=404)
    
    # Only owner can remove members
    if not budget.can_delete(user):
        return JsonResponse({'error': 'Only the owner can remove members'}, status=403)
    
    try:
        member = SharedBudgetMember.objects.get(id=member_id, shared_budget=budget)
    except SharedBudgetMember.DoesNotExist:
        return JsonResponse({'error': 'Member not found'}, status=404)
    
    # Can't remove yourself
    if member.user == user:
        return JsonResponse({'error': ' You cannot remove yourself. Use leave instead.'}, status=400)
    
    removed_username = member.user.username

    # Notify the removed member
    SharedBudgetNotification.objects.create(
        user=member.user,
        from_user=user,
        notification_type='member_left',
        shared_budget=budget,
        message=f'You were removed from budget "{budget.name}"'
    )

    member.delete()

    return JsonResponse({
        'message': f'Removed {removed_username} from budget'
    })

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
        budget = SharedBudget.objects.get(id=budget_id)
    except SharedBudget.DoesNotExist:
        return JsonResponse({'error': 'Shared budget not found'}, status=404)
    
    # Check permissions
    if not budget.can_edit(user):
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
    try:
        paid_by_user = User.objects.get(id=paid_by_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Paid by user not found'}, status=404)
    
    # Verify payer is a member
    if not budget.is_member(paid_by_user):
        return JsonResponse({'error': 'Payer must be a member of this budget'}, status=400)
    
    # Create expense
    expense = SharedExpense.objects.create(
        shared_budget=budget,
        description=data['description'],
        amount=amount,
        paid_by=paid_by_user,
        date=data.get('date', timezone.now().date().isoformat()),
        category=data.get('category', ''),
        created_by=user,
        notes=data.get('notes','')
    )

    # Create splits based on type
    split_type = data.get('split_type', budget.default_split_type)

    if split_type == 'custom' and data.get('splits'):
        # Custom splits provided
        expense.create_percentage_splits()
    else:
        # Default: equal split
        expense.create_equal_splits()

    # Notify members
    notify_budget_members(
        budget, user, 'expense_added',
        f'{user.username} added "${expense.description}" (${amount}) to "{budget.name}"'
    )

    return JsonResponse({
        'message': 'Expense added succesfully',
        'expense': serialize_expense(expense),
    }, status=201)

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
        budget = SharedBudget.objects.get(id=budget_id)
    except SharedBudget.DoesNotExist:
        return JsonResponse({'error': 'Shared budget not found'}, status=404)
    
    if not budget.can_edit(user):
        return JsonResponse({'error': 'You do not have permission to edit expenses'}, status=403)

    try:
        expense = SharedExpense.objects.get(id=expense_id, shared_budget=budget)
    except SharedExpense.DoesNotExist:
        return JsonResponse({'error': 'Expense not found'}, status=404)
    

    # Update fields
    if 'description' in data:
        expense.description = data['description']
    if 'amount' in data:
        try:
            expense.amount = float(str(data['amount']))
        except Exception:
            return JsonResponse({'error': 'Invalid amount'}, status=400)
    if 'date' in data:
        expense.date = data['date']
    if 'category' in data:
        expense.category = data['category']
    if 'notes' in data:
        expense.notes = data['notes']

    expense.save()

    # Recalculate splits if amount changed
    if 'amount' in data:
        expense.splits.all().delete()

        split_type = data.get('split_type', budget.default_split_type)

        if split_type == 'custom' and data.get('splits'):
            expense.create_custom_splits(data['splits'])
        elif split_type == 'percentage':
            expense.create_percentage_splits()
        else:
            expense.create_equal_splits()
        
    # Notify members
    notify_budget_members(
        budget, user, 'expense_updated',
        f'{user.username} updated "{expense.description}" in "{budget.name}"'
    )

    return JsonResponse({
        'message': 'Expense updated succesfully',
        'expense': serialize_expense(expense),
    })


@csrf_exempt
@login_required_json
def delete_expense(request, budget_id, expense_id):
    """Delete an expense from a shared budget."""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    user = request.user

    try:
        budget = SharedBudget.objects.get(id=budget_id)
    except SharedBudget.DoesNotExist:
        return JsonResponse({'error': 'Shared budget not found'}, status=404)
    
    if not budget.can_edit(user):
        return JsonResponse({'error': 'You do not have permission to delete expenses'}, status=403)
    
    try:
        expense = SharedExpense.objects.get(id=expense_id, shared_budget=budget)
    except SharedExpense.DoesNotExist:
        return JsonResponse({'error': 'Expense not found'}, status=404)
    
    description = expense.description
    expense.delete()

    # Notify members
    notify_budget_members(
        budget, user, 'expense_updated',
        f'{user.username} deleted "{description}" from "{budget.name}"'
    )

    return JsonResponse({
        'message': f'Expense "{description}" deleted succesfully'
    })


@csrf_exempt
@login_required_json
def get_budget_expenses(request, budget_id):
    """Get all expenses for a shared budget."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    user = request.user

    try:
        budget = SharedBudget.objects.get(id=budget_id)
    except SharedBudget.DoesNotExist:
        return JsonResponse({'error': 'Shared budget not found'}, status=404)
    
    expenses = budget.expenses.all()

    # Optional filters
    category = request.GET.get('category')
    paid_by = request.GET.get('paid_by')

    if category:
        expenses = expenses.filter(category=category)
    if paid_by:
        expenses = expenses.filer(paid_by=paid_by)

    return JsonResponse({
        'expenses': [serialize_expense(e) for e in expenses],
        'total': float(expenses.aggregate(total=Sum('amount'))['total'] or 0),
        'count': expenses.count(),
    })


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
        budget = SharedBudget.objects.get(id=budget_id)
    except SharedBudget.DoesNotExist:
        return JsonResponse({'error': 'Shared budget not found'}, status=404)
    
    if not budget.is_member(user):
        return JsonResponse({'error': 'You are not a member of this budget'}, status=403)
    
    receiver_id = data.get('receiver_id')
    if not receiver_id:
        return JsonResponse({'error': 'receiver_id is required'}, status=400)
    
    try:
        receiver = User.objects.get(id=receiver_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Receiver not found'}, status=404)
    
    if not budget.is_member(user):
        return JsonResponse({'error': 'Receiver must be a member of this budget'}, status=400)
    
    if receiver == user:
        return JsonResponse({'error': 'You cannot settle with yourself'}, status=400)
    
    try:
        amount = float(str(data.get('amount',0)))
        if amount <= 0:
            return JsonResponse({'error': 'Amount must be positive'}, status=400)
    except Exception:
        return JsonResponse({'error': 'Invalid amount'}, status=400)
    
    # Create settlement
    settlement = Settlement.objects.create(
        shared_budget=budget,
        payer=user,
        receiver=receiver,
        amount=amount,
        date=data.get('date', timezone.now().date().isoformat()),
        notes=data.get('notes','')
    )

    # Notify receiver
    SharedBudgetNotification.objects.create(
        user=receiver,
        from_user=user,
        notification_type='settlement_made',
        shared_budget=budget,
        message=f'{user.username} paid you ${amount} for "{budget.name}"'
    )

    return JsonResponse({
        'message': f'Settlement of ${amount} recorded',
        'settlement': {
            'id': settlement.id,
            'payer': {
                'id': user.id,
                'username': user.username,
            },
            'receiver': {
                'id': receiver.id,
                'username': receiver.username,
            },
            'amount': float(amount),
            'date': settlement.date.isoformat(),
        }
    }, status=201)

@csrf_exempt
@login_required_json
def get_budget_debts(request, budget_id):
    """Get all debts/balances for a shared budget."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    user = request.user

    try:
        budget = SharedBudget.objects.get(id=budget_id)
    except SharedBudget.DoesNotExist:
        return JsonResponse({'error': 'Shared budget not found'}, status=404)
    
    if not budget.is_member(user):
        return JsonResponse({'error': 'You are not a member of this budget'}, status=403)
    
    debts = calculate_debts(budget)

    # Get user-specific debts
    user_owes = [d for d in debts if d['from_user']['id'] == user.id]
    user_owed = [d for d in debts if d['to_user']['id'] == user.id]

    return JsonResponse({
        'all_debts': debts,
        'you_owe': user_owes,
        'you_are_owed': user_owed,
        'is_settled': len(debts) == 0,
    })


# ================================= NOTIFICATIONS =====================================

@csrf_exempt
@login_required_json
def get_budget_notifications(request):
    """Get shared budget notification for the logged-in user."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    user = request.user
    unread_only = request.GET.get('unread_only', 'false').lower() == 'true'

    notifcations = SharedBudgetNotification.objects.filter(user=user)

    if unread_only:
        notifcations = notifcations.filter(is_read=False)
    
    notifcations = notifcations[:50]

    notifcations_data = [{
        'id': n.id,
        'type': n.notification_type,
        'mesage': n.message,
        'from_user': {
            'id': n.from_user.id,
            'username': n.from_user.username,
        },
        'budget': {
            'id': n.shared_budget.id,
            'name': n.shared_budget.name,
        } if n.shared_budget else None,
        'is_read': n.is_read,
        'created_at': n.created_at.isoformat(),
    } for n in notifcations]

    unread_count = SharedBudgetNotification.objects.filter(user=user, is_read=False).count()

    return JsonResponse({
        'notifications': notifcations_data,
        'unread_count': unread_count,
    })

