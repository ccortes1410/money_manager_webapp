from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
import json
from functools import wraps

from ..models.friendship import Friendship, FriendshipNotification


def login_required_json(view_func):
    """Decorator to check if user is authenticated."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper

@csrf_exempt
@login_required_json
def get_friends(request):
    """Get all friends for the logged-in user."""
    if request.method != 'GET':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)
    
    user = request.user
    friends = Friendship.get_friends(user)

    friends_data = []
    for friend in friends:
        # Get friendship to find when they become friends
        friendship = Friendship.objects.filter(
            Q(sender=user, receiver=friend, status='accepted') |
            Q(sender=friend, receiver=user, status='accepted')
        ).first()

        friends_data.append({
            'id': friend.id,
            'username': friend.username,
            'email': friend.email,
            'first_name': friend.first_name,
            'last_name': friend.last_name,
            'friends_since': friendship.updated_at.isoformat() if friendship else None,
        })
    
    return JsonResponse({
        'friends': friends_data,
        'count': len(friends_data)
    })

@csrf_exempt
@login_required_json
def get_pending_requests(request):
    """Get pending friend requests for the logged-in user."""
    if request.method != 'GET':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)
    
    user = request.user

    # Received requests
    received = Friendship.get_pending_requests(user)
    received_data = [{
        'id': req.id,
        'from_user': {
            'id': req.sender.id,
            'username': req.sender.username,
            'email': req.sender.email,
            'first_name': req.sender.first_name,
            'last_name': req.sender.last_name,
        },
        'created_at': req.created_at.isoformat(),
    } for req in received]

    # Sent requests
    sent = Friendship.get_sent_requests(user)
    sent_data = [{
        'id': req.id,
        'from_user': {
            'id': req.receiver.id,
            'username': req.receiver.username,
            'email': req.receiver.email,
            'first_name': req.receiver.first_name,
            'last_name': req.receiver.last_name,
        },
        'created_at': req.created_at.isoformat(),
    } for req in sent]

    return JsonResponse({
        'received_requests': received_data,
        'sent_requests': sent_data,
        'received_count': len(received_data),
        'sent_count': len(sent_data),
    })

@csrf_exempt
@login_required_json
def send_friend_request(request):
    """Send a friend request to another user."""
    if request.method != 'POST':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    user = request.user

    # Get target user by username or email
    username = data.get('username')
    email = data.get('email')
    user_id = data.get('user_id')

    target_user = None
    
    if user_id:
        target_user = User.objects.filter(id=user_id).first()
    elif username:
        target_user = User.objects.filter(username__iexact=username).first()
    elif email:
        target_user = User.objects.filter(email__iexact=email).first()
    print("Target User:", target_user)
    if not target_user:
        return JsonResponse({"error": "User not found"}, status=404)
    
    # Check if blocked
    if Friendship.is_blocked(user, target_user):
        return JsonResponse({"error": "Unable to send friend request"}, status=400)
    
    # Check if already friends
    if Friendship.are_friends(user, target_user):
        return JsonResponse({"error": "You are already friends with this user"}, status=400)
    
    # Check if request already exists
    exisiting_request = Friendship.objects.filter(
        Q(sender=user, receiver=target_user) |
        Q(sender=target_user, receiver=user)
    ).exclude(status='declined').first()
    
    if exisiting_request:
        if exisiting_request.status == 'pending':
            if exisiting_request.sender == user:
                return JsonResponse({"error": "Friend request already sent"}, status=400)
            else:
                # They sent us a request, auto-accept
                exisiting_request.accept()

                # Create notification for the other user
                FriendshipNotification.objects.create(
                    user=target_user,
                    from_user=user,
                    notification_type='request_accepted',
                    message=f'{user.username} accepted your friend request'
                )

                return JsonResponse({
                    'message': 'Friend request accepted! Your are now friends.',
                    'friendship': {
                        'id': exisiting_request.id,
                        'status': 'accepted',
                        'friend': {
                            'id': target_user.id,
                            'username': target_user.username,
                        }
                    }
                })
        elif exisiting_request.status == 'accepted':
            return JsonResponse({"error": 'You are already friends with this user'}, status=400)
        elif exisiting_request.status == 'blocked':
            return JsonResponse({"error": 'Unable to send friend request'}, status=400)
        else:
            print("Unknown status:", {exisiting_request.status})
    # Create new friend request
    friendship = Friendship.objects.create(
        sender=user,
        receiver=target_user,
        status='pending'
    )
    print("Friendship:", friendship)
    # Create notification for target user
    FriendshipNotification.objects.create(
        user=target_user,
        from_user=user,
        notification_type='friend_request',
        friendship=friendship,
        message=f'{user.username} sent you a friend request'
    )

    return JsonResponse({
        'message': 'Friend request sent succesfully',
        'friendship': {
            'id': friendship.id,
            'status':friendship.status,
            'to_user': {
                'id': target_user.id,
                'username': target_user.username,
            }
        }
    }, status=201)


@csrf_exempt
@login_required_json
def respond_to_request(request, friendship_id):
    """Accept or decline a friend request."""
    if request.method != 'POST':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    user = request.user
    action = data.get('action')

    if action not in ['accept', 'decline']:
        return JsonResponse({'error': 'Invalid action. Use "accept" or "decline"'}, status=400)
    
    # Get the friendship
    try:
        friendship = Friendship.objects.get(id=friendship_id, receiver=user, status='pending')
    except Friendship.DoesNotExist:
        return JsonResponse({"error": "Friend request not found"}, status=404)
    
    if action == 'accept':
        friendship.accept()

        FriendshipNotification.objects.create(
            user=friendship.sender,
            from_user=user,
            notification_type='request_accepted',
            friendship=friendship,
            message=f'{user.username} accepted your friend request'
        )

        return JsonResponse({
            'message': 'Friend request accepted',
            'friend': {
                'id': friendship.sender.id,
                'username': friendship.sender.username,
                'email': friendship.sender.email,
            }
        })
    else:
        friendship.decline()

        return JsonResponse({
            'message': 'Friend request declined'
        })
    

@csrf_exempt
@login_required_json
def remove_friend(request, friend_id):
    """Remove a friend."""
    if request.method != 'DELETE':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)
    
    user = request.user

    try:
        friend = User.objects.get(id=friend_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    
    # Find and delete the friendship
    friendship =  Friendship.objects.filter(
        Q(sender=user, recevier=friend, status='accepted') |
        Q(sender=friend, receiver=user, status='accepted')
    ).first()

    if not friendship:
        return JsonResponse({"error": "Friendship not found"}, status=404)
    
    friendship.delete()

    return JsonResponse({
        'message': f'Removed {friend.username} from friends'
    })


@csrf_exempt
@login_required_json
def cancel_request(request, friendship_id):
    """Cancel a sent friend request."""
    if request.method != 'DELETE':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)
    
    user = request.user

    try:
        friendship = Friendship.objets.get(id=friendship_id, sender=user, status='pending')
    except Friendship.DoesNotExist:
        return JsonResponse({"error": "Friend request not found"}, status=404)
    
    friendship.delete()

    return JsonResponse({
        'message': 'Friend request cancelled'
    })

@login_required_json
def search_users(request):
    """Search for users to add as friends."""
    if request.method != 'GET':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)
    
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({"error": "Search query must be at least 2 characters"}, status=400)
    
    user = request.user

    # Search by username or email 
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(email__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    ).exclude(id=user.id)[:20]  # Limit results

    # Get existing friendships/requests
    existing = Friendship.objects.filter(
        Q(sender=user) | Q(receiver=user)
    ).exclude(status='declined')

    # Build a map of user_id -> relationship status
    relationship_map = {}
    for f in existing:
        other_user_id = f.receiver.id if f.sender == user else f.sender.id
        if f.status == 'accepted':
            relationship_map[other_user_id] = 'friends'
        elif f.status == 'pending':
            if f.sender == user:
                relationship_map[other_user_id] = 'request_sent'
            else:
                relationship_map[other_user_id] = 'request_received'
        elif f.status == 'blocked':
            relationship_map[other_user_id] = 'blocked'

    users_data = []
    for u in users:
        # Skip blocked users
        if relationship_map.get(u.id) == 'blocked':
            continue

        users_data.append({
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'relationship': relationship_map.get(u.id, 'none')
        })

    return JsonResponse({
        'users': users_data,
        'count': len(users_data)
    })


@login_required_json
def get_notifications(request):
    """Get friend notifications for the logged-in user."""
    if request.method != 'GET':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)
    
    user = request.user
    unread_only = request.GET.get('unread_only', 'false').lower() == 'true'

    notifications = FriendshipNotification.objects.filter(user=user)

    if unread_only:
        notifications = notifications.filter(is_read=False)

    notifications = notifications[:50] # Limit results

    notifications_data = [{
        'id': n.id,
        'type': n.notification_type,
        'message': n.message,
        'from_user': {
            'id': n.from_user.id,
            'username': n.from_user.username,
        },
        'is_read': n.is_read,
        'created_at': n.created_at.isoformat(),
        'friendship_id': n.friendship.id if n.friendship else None,
    } for n in notifications]

    unread_count = FriendshipNotification.objects.filter(user=user, is_read=False).count()

    return JsonResponse({
        'notifications': notifications_data,
        'unread_count': unread_count
    })


@csrf_exempt
@login_required_json
def mark_notification_read(request, notification_id):
    """Mark a notification as read."""
    if request.method != 'POST':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)
    
    user = request.user

    try:
        notification = FriendshipNotification.objects.get(id=notification_id, user=user)
    except FriendshipNotification.DoesNotExist:
        return JsonResponse({'error': 'Notification not found'}, status=404)

    notification.mark_as_read()

    return JsonResponse({'message': 'Notification marked as read'})


@csrf_exempt
@login_required_json
def mark_all_notifications_read(request):
    """Mark all notifications as read."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    user = request.user
    FriendshipNotification.objects.filter(user=user, is_read=False).update(is_read=True)

    return JsonResponse({'message': 'All notifications marked as read'})
