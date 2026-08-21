from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from functools import wraps
import json

from ..restapi import get_request, post_request, patch_request, delete_request
from ..services.api_adapters import (
    friendship_from_row,
    friendship_notification_from_row,
    get_username,
    get_user_first_name,
    get_user_last_name,
    get_user_email,
    get_user_data
)


def login_required_json(view_func):
    """Decorator to check if user is authenticated."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper


def _iso_date(dt):
    """Normalize a datetime or date into a plain YYYY-MM-DD string."""
    return dt.date().isoformat() if hasattr(dt, "date") else dt.isoformat()


# ======================= FRIENDSHIP CRUD ==============================

@csrf_exempt
@login_required_json
def get_friends(request):
    """Get all friends for the logged-in user."""
    if request.method != 'GET':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)

    user = request.user

    try:
        # Get friendships where user is involved and status is accepted
        # Check both sender and receiver sides
        friendship_rows_sender = get_request("friendships/", sender=user.id, status='accepted') or []
        friendship_rows_receiver = get_request("friendships/", receiver=user.id, status='accepted') or []
        friendship_rows = friendship_rows_sender + friendship_rows_receiver

        friends_data = []
        for friendship_row in friendship_rows:
            # Get the friend user data (the other person in the friendship)
            friend_id = friendship_row.get("receiver") if friendship_row.get("sender") == user.id else friendship_row.get("sender")
            if friend_id is not None:
                friend_row = get_request(f"users/{friend_id}")

                if friend_row:
                    friends_data.append({
                    'id': friend_id,
                    'username': get_username(friend_id),
                    'email': get_user_email(friend_id),
                    'first_name': get_user_first_name(friend_id),
                    'last_name': get_user_last_name(friend_id),
                    'friends_since': friendship_row.get("updated_at", ""),
                })
        return JsonResponse({
            'friends': friends_data,
            'count': len(friends_data)
        })
    except Exception as e:
        print(f"Error fetching friends: {e}")
        return JsonResponse({"error": "Failed to fetch friends"}, status=500)


@csrf_exempt
@login_required_json
def get_pending_requests(request):
    """Get pending friend requests for the logged-in user."""
    if request.method != 'GET':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)

    user = request.user

    try:
        # Received requests (where user is receiver)
        received_rows = get_request("friendships/", receiver=user.id, status='pending') or []
        received_data = []
        for req in received_rows:
            received_data.append({
                'id': req.get("id"),
                'from_user': {
                    'id': req.get("sender"),
                    'username': get_username(req.get("sender")) if req.get("sender") else f"user_{req.get('sender')}",
                    'email': get_user_email(req.get("sender")) if req.get("sender") else "",
                    'first_name': get_user_first_name(req.get("sender")) if req.get("sender") else "",
                    'last_name': get_user_last_name(req.get("sender")) if req.get("sender") else "",
                },
                'created_at': req.get("created_at"),
            })

        # Sent requests (where user is sender)
        sent_rows = get_request("friendships/", sender=user.id, status='pending') or []
        sent_data = []
        for req in sent_rows:
            sent_data.append({
                'id': req.get("id"),
                'to_user': {
                    'id': req.get("receiver"),
                    'username': get_username(req.get("receiver")) if req.get("receiver") else f"user_{req.get('receiver')}",
                    'email': get_user_email(req.get("receiver")) if req.get("receiver") else "",
                    'first_name': get_user_first_name(req.get("receiver")) if req.get("receiver") else "",
                    'last_name': get_user_last_name(req.get("receiver")) if req.get("receiver") else "",
                },
                'created_at': req.get("created_at"),
            })

        return JsonResponse({
            'received_requests': received_data,
            'sent_requests': sent_data,
            'received_count': len(received_data),
            'sent_count': len(sent_data),
        })
    except Exception as e:
        print(f"Error fetching pending requests: {e}")
        return JsonResponse({"error": "Failed to fetch pending requests"}, status=500)


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
        target_user_response = get_request(f"users/{user_id}")
        target_user = target_user_response.json() if hasattr(target_user_response, 'json') else target_user_response
    elif username:
        # Search for user by username
        users_response = get_request("users/", username__iexact=username)
        users = users_response.json() if hasattr(users_response, 'json') else (users_response or [])
        target_user = users[0] if users else None
    elif email:
        # Search for user by email
        users_response = get_request("users/", email__iexact=email)
        users = users_response.json() if hasattr(users_response, 'json') else (users_response or [])
        target_user = users[0] if users else None

    if not target_user:
        return JsonResponse({"error": "User not found"}, status=404)

    try:
        # Check if blocked (would need to check friendships with blocked status)
        # For now, we'll check via API if such endpoint exists
        # Alternatively, we can rely on the Node.js backend to handle this

        # Check if already friends
        existing_friendship_response = get_request("friendships/",
                                                 sender=user.id,
                                                 receiver=target_user["id"],
                                                 status='accepted')
        existing_friendship = existing_friendship_response.json() if hasattr(existing_friendship_response, 'json') else (existing_friendship_response or [])
        existing_friendship_reverse_response = get_request("friendships/",
                                                          sender=target_user["id"],
                                                          receiver=user.id,
                                                          status='accepted')
        existing_friendship_reverse = existing_friendship_reverse_response.json() if hasattr(existing_friendship_reverse_response, 'json') else (existing_friendship_reverse_response or [])
        if existing_friendship or existing_friendship_reverse:
            return JsonResponse({"error": "You are already friends with this user"}, status=400)

        # Check if request already exists (pending in either direction)
        existing_request_response = get_request("friendships/",
                                              sender=user.id,
                                              receiver=target_user["id"],
                                              status='pending')
        existing_request = existing_request_response.json() if hasattr(existing_request_response, 'json') else (existing_request_response or [])
        existing_request_reverse_response = get_request("friendships/",
                                                     sender=target_user["id"],
                                                     receiver=user.id,
                                                     status='pending')
        existing_request_reverse = existing_request_reverse_response.json() if hasattr(existing_request_reverse_response, 'json') else (existing_request_reverse_response or [])

        if existing_request:
            if existing_request and len(existing_request) > 0 and existing_request[0].get("sender") == user.id:
                return JsonResponse({"error": "Friend request already sent"}, status=400)
            else:
                # They sent us a request, auto-accept
                if existing_request and len(existing_request) > 0:
                    friendship_row = patch_request(f"friendships/{existing_request[0].get('id')}", {'status': 'accepted'})
                    friendship_row = friendship_row.json() if hasattr(friendship_row, 'json') else friendship_row

                    # Create notification for the other user
                    post_request("friendship-notifications/", {
                        'user_id': target_user.get("id") if target_user else None,
                        'from_user_id': user.id,
                        'notification_type': 'request_accepted',
                        'message': f'{user.username} accepted your friend request'
                    })

                    friendship = friendship_from_row(friendship_row) if friendship_row else None
                    return JsonResponse({
                        'message': 'Friend request accepted! You are now friends.',
                        'friendship': {
                            'id': friendship.id if friendship else (existing_request[0].get("id") if existing_request and len(existing_request) > 0 else None),
                            'status': 'accepted',
                            'friend': {
                                'id': target_user.get("id") if target_user else None,
                                'username': target_user.get("username") if target_user else None,
                            }
                        }
                    })
                else:
                    return JsonResponse({"error": "Invalid request data"}, status=400)
        elif existing_request_reverse:
            # They sent us a request, auto-accept
            if existing_request_reverse and len(existing_request_reverse) > 0:
                friendship_row = patch_request(f"friendships/{existing_request_reverse[0].get('id')}", {'status': 'accepted'})
                friendship_row = friendship_row.json() if hasattr(friendship_row, 'json') else friendship_row

                # Create notification for the other user
                post_request("friendship-notifications/", {
                    'user_id': target_user.get("id") if target_user else None,
                    'from_user_id': user.id,
                    'notification_type': 'request_accepted',
                    'message': f'{user.username} accepted your friend request'
                })

                friendship = friendship_from_row(friendship_row) if friendship_row else None
                return JsonResponse({
                    'message': 'Friend request accepted! You are now friends.',
                    'friendship': {
                        'id': friendship.id if friendship else (existing_request_reverse[0].get("id") if existing_request_reverse and len(existing_request_reverse) > 0 else None),
                        'status': 'accepted',
                        'friend': {
                            'id': target_user.get("id") if target_user else None,
                            'username': target_user.get("username") if target_user else None,
                        }
                    }
                })
            else:
                return JsonResponse({"error": "Invalid request data"}, status=400)

        # Create new friend request
        friendship_row = post_request("friendships/", {
            'sender': user.id,
            'receiver': target_user.get("id") if target_user else None,
            'status': 'pending'
        })
        friendship_row = friendship_row.json() if hasattr(friendship_row, 'json') else friendship_row

        if not friendship_row:
            return JsonResponse({'error': 'Failed to send friend request'}, status=500)

        # Create notification for target user
        post_request("friendship-notifications/", {
            'user_id': target_user.get("id") if target_user else None,
            'from_user_id': user.id,
            'notification_type': 'friend_request',
            'message': f'{user.username} sent you a friend request'
        })

        friendship = friendship_from_row(friendship_row)

        return JsonResponse({
            'message': 'Friend request sent successfully',
            'friendship': {
                'id': friendship.id,
                'status': friendship.status,
                'to_user': {
                    'id': target_user.get("id") if target_user else None,
                    'username': target_user.get("username") if target_user else None,
                }
            }
        }, status=201)
    except Exception as e:
        print(f"Error sending friend request: {e}")
        return JsonResponse({'error': 'Failed to send friend request'}, status=500)


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

    try:
        # Get the friendship and verify it belongs to the user
        friendship_response = get_request(f"friendships/{friendship_id}")
        friendship_row = friendship_response.json() if hasattr(friendship_response, 'json') else friendship_response
        if not friendship_row:
            return JsonResponse({"error": "Friend request not found"}, status=404)

        # Verify the user is the receiver
        if friendship_row.get("receiver") != user.id:
            return JsonResponse({"error": "Friend request not found"}, status=404)

        # Verify it's pending
        if friendship_row.get("status") != 'pending':
            return JsonResponse({"error": "Friend request is not pending"}, status=400)

        if action == 'accept':
            # Accept the friendship
            updated_friendship_response = patch_request(f"friendships/{friendship_id}", {'status': 'accepted'})
            updated_friendship_row = updated_friendship_response.json() if hasattr(updated_friendship_response, 'json') else updated_friendship_response
            if not updated_friendship_row:
                return JsonResponse({'error': 'Failed to accept friend request'}, status=500)

            # Create notification for the sender
            post_request("friendship-notifications/", {
                'user_id': friendship_row["sender"],
                'from_user_id': user.id,
                'notification_type': 'request_accepted',
                'message': f'{user.username} accepted your friend request'
            })

            friendship = friendship_from_row(updated_friendship_row)
            sender_response = get_request(f"users/{friendship_row['sender']}")
            sender_row = sender_response.json() if hasattr(sender_response, 'json') else sender_response

            return JsonResponse({
                'message': 'Friend request accepted',
                'friend': {
                    'id': sender_row["id"] if sender_row else friendship_row.get("sender"),
                    'username': sender_row["username"] if sender_row else f"user_{friendship_row.get('sender')}",
                    'email': sender_row["email"] if sender_row else "",
                }
            })
        else:
            # Decline the friendship
            updated_friendship_response = patch_request(f"friendships/{friendship_id}", {'status': 'declined'})
            updated_friendship_row = updated_friendship_response.json() if hasattr(updated_friendship_response, 'json') else updated_friendship_response
            if not updated_friendship_row:
                return JsonResponse({'error': 'Failed to decline friend request'}, status=500)

            return JsonResponse({
                'message': 'Friend request declined'
            })
    except Exception as e:
        print(f"Error responding to friend request: {e}")
        return JsonResponse({'error': 'Failed to process friend request'}, status=500)


@csrf_exempt
@login_required_json
def remove_friend(request, friend_id):
    """Remove a friend."""
    if request.method != 'DELETE':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)

    user = request.user

    try:
        # Verify friend exists
        friend_response = get_request(f"users/{friend_id}")
        friend_row = friend_response.json() if hasattr(friend_response, 'json') else friend_response
        if not friend_row:
            return JsonResponse({"error": "User not found"}, status=404)

        # Find and delete the friendship (accepted status)
        friendship_response_sender = get_request("friendships/",
                                              sender=user.id,
                                              receiver=friend_id,
                                              status='accepted')
        friendship_rows_sender = friendship_response_sender.json() if hasattr(friendship_response_sender, 'json') else (friendship_response_sender or [])
        friendship_response_receiver = get_request("friendships/",
                                                sender=friend_id,
                                                receiver=user.id,
                                                status='accepted')
        friendship_rows_receiver = friendship_response_receiver.json() if hasattr(friendship_response_receiver, 'json') else (friendship_response_receiver or [])

        friendship_to_delete = None
        if friendship_rows_sender and len(friendship_rows_sender) > 0:
            friendship_to_delete = friendship_rows_sender[0]
        elif friendship_rows_receiver and len(friendship_rows_receiver) > 0:
            friendship_to_delete = friendship_rows_receiver[0]

        if not friendship_to_delete:
            return JsonResponse({"error": "Friendship not found"}, status=404)

        # Delete via API
        result = delete_request(f"friendships/{friendship_to_delete.get('id')}") if friendship_to_delete else None
        if result is None:
            return JsonResponse({'error': 'Failed to remove friend'}, status=500)

        return JsonResponse({
            'message': f'Removed {friend_row.get("username", "unknown user")} from friends'
        })
    except Exception as e:
        print(f"Error removing friend: {e}")
        return JsonResponse({'error': 'Failed to remove friend'}, status=500)


@csrf_exempt
@login_required_json
def cancel_request(request, friendship_id):
    """Cancel a sent friend request."""
    if request.method != 'DELETE':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)

    user = request.user

    try:
        # Get the friendship and verify it belongs to the user (as sender) and is pending
        friendship_response = get_request(f"friendships/{friendship_id}")
        friendship_row = friendship_response.json() if hasattr(friendship_response, 'json') else friendship_response
        if not friendship_row:
            return JsonResponse({"error": "Friend request not found"}, status=404)

        # Verify the user is the sender
        if friendship_row.get("sender") != user.id:
            return JsonResponse({"error": "Friend request not found"}, status=404)

        # Verify it's pending
        if friendship_row.get("status") != 'pending':
            return JsonResponse({"error": "Friend request is not pending"}, status=400)

        # Delete via API
        result = delete_request(f"friendships/{friendship_id}")
        if result is None:
            return JsonResponse({'error': 'Failed to cancel friend request'}, status=500)

        return JsonResponse({
            'message': 'Friend request cancelled'
        })
    except Exception as e:
        print(f"Error canceling friend request: {e}")
        return JsonResponse({'error': 'Failed to cancel friend request'}, status=500)


@login_required_json
def search_users(request):
    """Search for users to add as friends."""
    if request.method != 'GET':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)

    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({"error": "Search query must be at least 2 characters"}, status=400)

    user = request.user

    try:
        # Search by username, email, first_name, or last_name
        users_response = get_request("users/", username__icontains=query)
        users = users_response.json() if hasattr(users_response, 'json') else (users_response or [])

        # Also search by email if no results from username
        if not users:
            users_response = get_request("users/", email__icontains=query)
            users = users_response.json() if hasattr(users_response, 'json') else (users_response or [])

        # Also search by first_name
        if not users:
            users_response = get_request("users/", first_name__icontains=query)
            users = users_response.json() if hasattr(users_response, 'json') else (users_response or [])

        # Also search by last_name
        if not users:
            users_response = get_request("users/", last_name__icontains=query)
            users = users_response.json() if hasattr(users_response, 'json') else (users_response or [])

        # Limit results and exclude current user
        users = [u for u in users if u["id"] != user.id][:20]

        # Get existing friendships/requests to determine relationship status
        friendship_response_sender = get_request("friendships/", sender=user.id)
        friendship_rows_sender = friendship_response_sender.json() if hasattr(friendship_response_sender, 'json') else (friendship_response_sender or [])
        friendship_response_receiver = get_request("friendships/", receiver=user.id)
        friendship_rows_receiver = friendship_response_receiver.json() if hasattr(friendship_response_receiver, 'json') else (friendship_response_receiver or [])
        friendship_rows = friendship_rows_sender + friendship_rows_receiver

        # Filter out declined friendships
        friendship_rows = [f for f in friendship_rows if f.get("status") != 'declined']

        # Build a map of user_id -> relationship status
        relationship_map = {}
        for f in friendship_rows:
            other_user_id = f["receiver"] if f["sender"] == user.id else f["sender"]
            if f.get("status") == 'accepted':
                relationship_map[other_user_id] = 'friends'
            elif f.get("status") == 'pending':
                if f["sender"] == user.id:
                    relationship_map[other_user_id] = 'request_sent'
                else:
                    relationship_map[other_user_id] = 'request_received'
            elif f.get("status") == 'blocked':
                relationship_map[other_user_id] = 'blocked'

        users_data = []
        for u in users:
            # Skip blocked users
            if relationship_map.get(u["id"]) == 'blocked':
                continue

            users_data.append({
                'id': u["id"],
                'username': u["username"],
                'email': u["email"],
                'first_name': u["first_name"],
                'last_name': u["last_name"],
                'relationship': relationship_map.get(u["id"], 'none')
            })

        return JsonResponse({
            'users': users_data,
            'count': len(users_data)
        })
    except Exception as e:
        print(f"Error searching users: {e}")
        return JsonResponse({'error': 'Failed to search users'}, status=500)


@login_required_json
def get_notifications(request):
    """Get friend notifications for the logged-in user."""
    if request.method != 'GET':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)

    user = request.user
    unread_only = request.GET.get('unread_only', 'false').lower() == 'true'

    try:
        # Get notifications
        notification_response = get_request("friendship-notifications/", user_id=user.id)
        notification_rows = notification_response.json() if hasattr(notification_response, 'json') else (notification_response or [])

        if unread_only:
            notification_rows = [n for n in notification_rows if not n.get("is_read", False)]

        # Sort by date descending and limit to 50
        notification_rows.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        notification_rows = notification_rows[:50]

        notifications_data = []
        for notification_row in notification_rows:
            from_user_response = get_request(f"users/{notification_row['from_user_id']}")
            from_user_row = from_user_response.json() if hasattr(from_user_response, 'json') else from_user_response

            notifications_data.append({
                'id': notification_row["id"],
                'type': notification_row["notification_type"],
                'message': notification_row["message"],
                'from_user': {
                    'id': notification_row["from_user_id"],
                    'username': from_user_row["username"] if from_user_row else f"user_{notification_row['from_user_id']}",
                },
                'is_read': notification_row.get("is_read", False),
                'created_at': notification_row.get("created_at"),
                'friendship_id': notification_row.get("friendship_id"),
            })

        unread_count = len([n for n in notification_rows if not n.get("is_read", False)])

        return JsonResponse({
            'notifications': notifications_data,
            'unread_count': unread_count
        })
    except Exception as e:
        print(f"Error getting notifications: {e}")
        return JsonResponse({'error': 'Failed to get notifications'}, status=500)


@csrf_exempt
@login_required_json
def mark_notification_read(request, notification_id):
    """Mark a notification as read."""
    if request.method != 'POST':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)

    user = request.user

    try:
        # Get notification and verify it belongs to the user
        notification_row = get_request(f"friendship-notifications/{notification_id}")
        if not notification_row:
            return JsonResponse({'error': 'Notification not found'}, status=404)

        # Verify the user is the recipient
        if notification_row["user_id"] != user.id:
            return JsonResponse({'error': 'Notification not found'}, status=404)

        # Mark as read via API
        updated_notification_row = patch_request(f"friendship-notifications/{notification_id}", {'is_read': True})
        if not updated_notification_row:
            return JsonResponse({'error': 'Failed to mark notification as read'}, status=500)

        return JsonResponse({'message': 'Notification marked as read'})
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        return JsonResponse({'error': 'Failed to mark notification as read'}, status=500)


@csrf_exempt
@login_required_json
def mark_all_notifications_read(request):
    """Mark all notifications as read."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)

    user = request.user

    try:
        # Mark all unread notifications as read via API
        # First get all unread notifications for the user
        unread_notifications = get_request("friendship-notifications/", user_id=user.id, is_read=False) or []

        # Update each one
        for notification in unread_notifications:
            patch_request(f"friendship-notifications/{notification['id']}", {'is_read': True})

        return JsonResponse({'message': 'All notifications marked as read'})
    except Exception as e:
        print(f"Error marking all notifications as read: {e}")
        return JsonResponse({'error': 'Failed to mark all notifications as read'}, status=500)