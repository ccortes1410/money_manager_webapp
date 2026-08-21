"""
Tests for Friendship model and its API endpoints.
"""
import json
from django.urls import reverse
from django.utils import timezone

from djangoapp.models.friendship import Friendship

from .test_base import BaseTestCase
from .test_api_backend import TestApiBackend
from unittest.mock import patch


class FriendshipModelTests(BaseTestCase):
    def test_create_friendship_usual(self):
        friendship = Friendship.objects.create(sender=self.user1, receiver=self.user2)
        self.assertEqual(friendship.status, 'pending')

    def test_str_representation(self):
        friendship = Friendship.objects.create(sender=self.user1, receiver=self.user2)
        expected = f"{self.user1.username} -> {self.user2.username} (pending)"
        self.assertEqual(str(friendship), expected)

    def test_unique_together_sender_receiver(self):
        from django.db import IntegrityError, transaction
        Friendship.objects.create(sender=self.user1, receiver=self.user2)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Friendship.objects.create(sender=self.user1, receiver=self.user2)

    def test_reverse_pair_is_a_distinct_row(self):
        Friendship.objects.create(sender=self.user1, receiver=self.user2)
        reverse_friendship = Friendship.objects.create(sender=self.user2, receiver=self.user1)
        self.assertIsNotNone(reverse_friendship.id)

    def test_accept(self):
        friendship = Friendship.objects.create(sender=self.user1, receiver=self.user2)
        friendship.accept()
        friendship.refresh_from_db()
        self.assertEqual(friendship.status, 'accepted')

    def test_decline(self):
        friendship = Friendship.objects.create(sender=self.user1, receiver=self.user2)
        friendship.decline()
        friendship.refresh_from_db()
        self.assertEqual(friendship.status, 'declined')

    def test_are_friends_true_regardless_of_direction(self):
        Friendship.objects.create(sender=self.user1, receiver=self.user2, status='accepted')
        self.assertTrue(Friendship.are_friends(self.user1, self.user2))
        self.assertTrue(Friendship.are_friends(self.user2, self.user1))

    def test_are_friends_false_when_pending(self):
        Friendship.objects.create(sender=self.user1, receiver=self.user2, status='pending')
        self.assertFalse(Friendship.are_friends(self.user1, self.user2))

    def test_get_friends_returns_correct_users_both_directions(self):
        Friendship.objects.create(sender=self.user1, receiver=self.user2, status='accepted')
        Friendship.objects.create(sender=self.user3, receiver=self.user1, status='accepted')
        friends = Friendship.get_friends(self.user1)
        self.assertIn(self.user2, friends)
        self.assertIn(self.user3, friends)
        self.assertEqual(len(friends), 2)

    def test_get_pending_and_sent_requests(self):
        Friendship.objects.create(sender=self.user2, receiver=self.user1, status='pending')
        Friendship.objects.create(sender=self.user1, receiver=self.user3, status='pending')

        received = Friendship.get_pending_requests(self.user1)
        sent = Friendship.get_sent_requests(self.user1)

        self.assertEqual(received.count(), 1)
        self.assertEqual(received.first().sender, self.user2)
        self.assertEqual(sent.count(), 1)
        self.assertEqual(sent.first().receiver, self.user3)

    def test_is_blocked_either_direction(self):
        Friendship.objects.create(sender=self.user1, receiver=self.user2, status='blocked')
        self.assertTrue(Friendship.is_blocked(self.user1, self.user2))
        self.assertTrue(Friendship.is_blocked(self.user2, self.user1))
        self.assertFalse(Friendship.is_blocked(self.user1, self.user3))


class FriendshipAPITests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user1)
        # Set up mock API
        self.test_api = TestApiBackend()
        self.get_patcher = patch('djangoapp.restapi.requests.get', side_effect=self.test_api.get)
        self.post_patcher = patch('djangoapp.restapi.requests.post', side_effect=self.test_api.post)
        self.patch_patcher = patch('djangoapp.restapi.requests.patch', side_effect=self.test_api.patch)
        self.delete_patcher = patch('djangoapp.restapi.requests.delete', side_effect=self.test_api.delete)
        self.get_patcher.start()
        self.post_patcher.start()
        self.patch_patcher.start()
        self.delete_patcher.start()

    def tearDown(self):
        self.get_patcher.stop()
        self.post_patcher.stop()
        self.patch_patcher.stop()
        self.delete_patcher.stop()
        super().tearDown()


    def _seed_user(self, username_suffix="", **overrides):
        """Helper to seed a user via the mock API."""
        base_data = {
            "username": f"testuser{username_suffix}",
            "email": f"testuser{username_suffix}@example.com",
            "first_name": f"Test{username_suffix}",
            "last_name": "User",
        }
        base_data.update(overrides)
        return self.test_api.seed("users", base_data)

    def _seed_friendship(self, **overrides):
        """Helper to seed a frienship via the mock API."""
        base_data = {
            "sender": self.user1.id,
            "receiver": self.user2.id,
            "status": "pending",
        }
        base_data.update(overrides)
        return self.test_api.seed("friendships", base_data)
    
    def test_get_friends_requires_auth(self):
        self.client.logout()
        response = self.client.get(reverse('djangoapp:get_friends'))
        self.assertEqual(response.status_code, 401)

    def test_get_friends_returns_accepted_friends_only(self):
        # Seed users
        user2_data = self._seed_user("2")
        user3_data = self._seed_user("3")

        # Seed friendships - one accepted, one pending
        self._seed_friendship(status='accepted', receiver=user2_data['id'])  # user1 -> user2 (accepted)
        self._seed_friendship(status='pending', receiver=user3_data['id'])  # user 1 -> user3 (pending)

        response = self.client.get(reverse('djangoapp:get_friends'))
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data['count'], 1)
        self.assertEqual(data['friends'][0]['username'], 'testuser2')

    def test_get_pending_requests_endpoint(self):
        # Seed users
        user2_data = self._seed_user("2")
        user3_data = self._seed_user("3")

        # Seed pending requests - one received, one sent
        self._seed_friendship(status='pending', receiver=self.user1.id, sender=user2_data['id']) # user2 -> user1 (received)
        self._seed_friendship(status='pending', receiver=user3_data['id'], sender=self.user1.id)  # user1 -> user3 (sent)

        response = self.client.get(reverse('djangoapp:get_pending_requests'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['received_count'], 1)
        self.assertEqual(data['sent_count'], 1)
        self.assertEqual(data['received_requests'][0]['from_user']['username'], 'testuser2')
        self.assertEqual(data['sent_requests'][0]['to_user']['username'], 'testuser3')

    def test_send_friend_request_by_username(self):
        # Seed target user
        target_user = self._seed_user("2")

        response = self.client.post(
            reverse('djangoapp:send_friend_request'),
            data=json.dumps({'username': target_user['username']}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

        # Check that the friendship was added to the mock API
        friendships = self.test_api.resources.get("friendships", [])
        self.assertEqual(len(friendships), 1)
        self.assertEqual(friendships[0]['sender'], self.user1.id)
        self.assertEqual(friendships[0]['receiver'], target_user['id'])
        self.assertEqual(friendships[0]['status'], 'pending')

    def test_send_friend_request_auto_accepts_existing_reverse_request(self):
        # Seed target user
        target_user = self._seed_user("2")

        # Seed existing reverse request (targer user sent request to current user)
        self._seed_friendship(status='pending', sender=target_user['id'], receiver=self.user1.id)
        response = self.client.post(
            reverse('djangoapp:send_friend_request'),
            data=json.dumps({'username': target_user['username']}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Check that the friendship is now accepted
        friendships = self.test_api.resources.get("friendships", [])
        self.assertEqual(len(friendships), 1)
        self.assertEqual(friendships[0]['status'], 'accepted')

    def test_send_friend_request_user_not_found(self):
        response = self.client.post(
            reverse('djangoapp:send_friend_request'),
            data=json.dumps({'username': 'nonexistentuser'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    def test_respond_to_request_accept(self):
        # Seed users and friendship
        target_user = self._seed_user("2")
        friendship = self._seed_friendship(status='pending', sender=target_user['id'], receiver=self.user1.id)

        response = self.client.post(
            reverse('djangoapp:respond_to_request', kwargs={'friendship_id': friendship['id']}),
            data=json.dumps({'action': 'accept'}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Check that the friendship was updated in the mock API
        updated_friendship = next((f for f in self.test_api.resources["friendships"] if f['id'] == friendship['id']), None)
        self.assertIsNotNone(updated_friendship)
        self.assertEqual(updated_friendship['status'], 'accepted')

    def test_respond_to_request_decline(self):
        # Seed users and friendship
        target_user = self._seed_user("2")
        friendship = self._seed_friendship(status='pending', sender=target_user['id'], receiver=self.user1.id)

        response = self.client.post(
            reverse('djangoapp:respond_to_request', kwargs={'friendship_id': friendship['id']}),
            data=json.dumps({'action': 'decline'}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Check that the friendship was updated in the mock API
        updated_friendship = next((f for f in self.test_api.resources["friendships"] if f['id'] == friendship['id']), None)
        self.assertIsNotNone(updated_friendship)
        self.assertEqual(updated_friendship['status'], 'declined')

    def test_cancel_request_success(self):
        # Seed users and friendship
        target_user = self._seed_user("2")
        friendship = self._seed_friendship(status='pending', sender=self.user1.id, receiver=target_user['id'])

        response = self.client.delete(
            reverse('djangoapp:cancel_request', kwargs={'friendship_id': friendship['id']}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Check that the friendship was deleted from the mock API
        friendships = self.test_api.resources.get("friendships", [])
        self.assertEqual(len(friendships), 0)

    def test_remove_friend_success(self):
        # Seed users and friendship
        target_user = self._seed_user("2")
        friendship = self._seed_friendship(status='accepted', sender=self.user1.id, receiver=target_user['id'])

        response = self.client.delete(
            reverse('djangoapp:remove_friend', kwargs={'friend_id': target_user['id']}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Check that the friendship was deleted from the mock API
        friendships = self.test_api.resources.get("friendships", [])
        self.assertEqual(len(friendships), 0)
    
    def test_search_users_finds_by_username(self):
        # Seed users to search
        self._seed_user("2", username="johndoe")
        self._seed_user("3", username="janedoe")

        response = self.client.get(reverse('djangoapp:search_users'), {'q': 'johndoe'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['users'][0]['username'], 'johndoe')

    def test_search_users_requires_minimum_length(self):
        response = self.client.get(reverse('djangoapp:search_users'), {'q': 'a'})
        self.assertEqual(response.status_code, 400)


class FriendshipNotificationAPITests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user1)
        # Set up mock API backend
        self.test_api = TestApiBackend()
        self.get_patcher = patch('djangoapp.restapi.requests.get', side_effect=self.test_api.get)
        self.post_patcher = patch('djangoapp.restapi.requests.post', side_effect=self.test_api.post)
        self.patch_patcher = patch('djangoapp.restapi.requests.patch', side_effect=self.test_api.patch)
        self.delete_patcher = patch('djangoapp.restapi.requests.delete', side_effect=self.test_api.delete)
        self.get_patcher.start()
        self.post_patcher.start()
        self.patch_patcher.start()
        self.delete_patcher.start()

    def tearDown(self):
        self.get_patcher.stop()
        self.post_patcher.stop()
        self.patch_patcher.stop()
        self.delete_patcher.stop()
        super().tearDown()

    def _seed_user(self, username_suffix="", **overrides):
        """Helper to seed a user via the mock API."""
        base_data = {
            "username": f"testuser{username_suffix}",
            "email": f"testuser{username_suffix}@example.com",
            "first_name": f"Test{username_suffix}",
            "last_name": "User"
        }
        base_data.update(overrides)
        return self.test_api.seed("users", base_data)

    def _seed_friendship_notification(self, **overrides):
        """Helper to seed a friendship notification via the mock API."""
        base_data = {
            "user_id": self.user1.id,
            "from_user_id": self.user2.id,
            "notification_type": "friend_request",
            "message": "Test notification",
            "is_read": False,
        }
        base_data.update(overrides)
        return self.test_api.seed("friendship-notifications", base_data)

    def test_get_notifications_requires_auth(self):
        self.client.logout()
        response = self.client.get(reverse('djangoapp:get_notifications'))
        self.assertEqual(response.status_code, 401)

    def test_get_notifications_returns_data(self):
        # Seed users
        self._seed_user("2")

        # Seed notification
        self._seed_friendship_notification()

        response = self.client.get(reverse('djangoapp:get_notifications'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['notifications']), 1)
        self.assertEqual(data['notifications'][0]['type'], 'friend_request')
        self.assertEqual(data['unread_count'], 1)

    def test_get_notifications_filter_unread_only(self):
        # Seed users
        self._seed_user("2")

        # Seed notifications - one read, one unread
        self._seed_friendship_notification(is_read=False)
        self._seed_friendship_notification(is_read=True)

        response = self.client.get(reverse('djangoapp:get_notifications'), {'unread_only': 'true'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['notifications']), 1)
        self.assertEqual(data['notifications'][0]['is_read'], False)
        self.assertEqual(data['unread_count'], 1)

    def test_mark_notification_read_success(self):
        # Seed users and notification
        self._seed_user("2")
        notification = self._seed_friendship_notification(is_read=False)

        response = self.client.post(
            reverse('djangoapp:mark_notification_read', kwargs={'notification_id': notification['id']}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Check that the notification was updated in the mock API
        updated_notification = next((n for n in self.test_api.resources["friendship-notifications"] if n['id']), None)
        self.assertIsNotNone(updated_notification)
        self.assertEqual(updated_notification['is_read'], True)

    def test_mark_all_notifications_read_success(self):
        # Seed users
        self._seed_user("2")

        # Seed multiple notifications
        self._seed_friendship_notification(is_read=False)
        self._seed_friendship_notification(is_read=False)

        response = self.client.post(
            reverse('djangoapp:mark_all_notifications_read'),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Check that all notifications were updated in the mock API
        notifications = self.test_api.resources.get("friendship-notifications", [])
        for notification in notifications:
            self.assertEqual(notification['is_read'], True)
