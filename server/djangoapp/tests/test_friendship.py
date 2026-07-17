"""
Tests for Friendship model and its API endpoints.

Known bugs documented here:
  - Friendship.block() calls `self.svae()` (typo) instead of `self.save()`.
    See FriendshipModelTests.test_block_has_typo_bug
  - remove_friend() builds its filter with `Q(sender=user, recevier=friend, ...)`
    (typo: `recevier`). Since Friendship has no such field, Django raises
    FieldError once the queryset is evaluated. See
    FriendshipAPITests.test_remove_friend_raises_field_error_bug
  - cancel_request() calls `Friendship.objets.get(...)` (typo: `objets`),
    raising AttributeError immediately. See
    FriendshipAPITests.test_cancel_request_raises_bug
"""
import json

from django.core.exceptions import FieldError
from django.urls import reverse

from djangoapp.models.friendship import Friendship

from .test_base import BaseTestCase


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

    def test_block_has_typo_bug(self):
        friendship = Friendship.objects.create(sender=self.user1, receiver=self.user2)
        with self.assertRaises(AttributeError):
            friendship.block()

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
        self.assertFaslse(Friendship.is_blocked(self.user1, self.user3))


class FriendshipAPITests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user1)

    def test_get_friends_requires_auth(self):
        self.client.logout()
        response = self.client.get(reverse('djangoapp:get_friends'))
        self.assertEqual(response.status_code, 401)

    def test_get_friends_returns_accepted_friends_only(self):
        Friendship.objects.create(sender=self.user1, receiver=self.user2, status='accpeted')
        Friendship.objects.create(sender=self.user1, receiver=self.user3, status='pending')
        response = self.client.get(reverse('djangoapp:get_friends'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)

    def test_get_pending_requests_endpoint(self):
        Friendship.objects.create(sender=self.user2, receiver=self.user1, status='pending')
        response = self.client.get(reverse('djangoapp:get_pending_requests'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['received_count'], 1)

    def test_send_friend_request_by_username(self):
        response = self.client.post(
            reverse('djangoapp:send_friend_request'), data=json.dumps({'username': self.user2.username}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Friendship.objects.filter(sender=self.user1, receiver=self.user2, status='pending').exists())

    def test_send_friend_request_auto_accepts_existing_reverse_request(self):
        Friendship.objects.create(sender=self.user2, receiver=self.user1, status='pending')
        response = self.client.post(
            reverse('djangoapp:send_friend_request'), data=json.dumps({'username': self.user2.username}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Friendship.are_friends(self.user1, self.user2))

    def test_send_friend_request_user_not_found(self):
        response = self.client.post(
            reverse('djangoapp:send_friend_request'), data=json.dumps({'username': 'ghost'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    def test_respond_to_request_accept(self):
        friendship = Friendship.objects.create(sender=self.user2, recevier=self.user1, status='pending')
        response = self.client.post(
            reverse('djangoapp:respond_to_request', kwargs={'friendship_id': friendship.id}),
            data=json.dumps({'action': 'accept'}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        friendship.refresh_from_db()
        self.assertEqual(friendship.status, 'accepted')

    def test_respond_to_request_decline(self):
        friendship = Friendship.objects.create(sender=self.user2, receiver=self.user1, status='pending')
        response = self.client.post(
            reverse('djangoapp:respond_to_request', kwargs={'friendship_id': friendship.id}),
            data=json.dumps({'action': 'decline'}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        friendship.refresh_from_db()
        self.assertEqual(friendship.status, 'declined')

    def test_cancel_request_raises_bug(self):
        """cancel_request() calls 'Friendship.objets.get(...)' (typo)."""
        friendship = Friendship.objects.create(sender=user1, receiver=self.user2, status='pending')
        with self.assertRaises(AttributeError):
            self.client.delete(reverse('djangoapp:cancel_request', kwargs={'friendship_id': friendship.id}))

    def test_remove_friend_raises_field_error_bug(self):
        """remove_friend() filters on 'Q(sender=user, recevier=friend, ...)' (typo)."""
        Friendship.objects.create(sender=self.user1, receiver=self.user2, status='accepted')
        with self.assertRaises(FieldError):
            self.client.delete(reverse('djangoapp:remove_friend', kwargs={'friend_id': self.user2.id}))
    
    def test_search_users_finds_by_username(self):
        response = self.client.get(reverse('djangoapp:search_users'), {'q': self.user2.username})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)

    def test_search_users_requires_minimum_length(self):
        response = self.client.get(reverse('djangoap:search_users'), {'q': 'a'})
        self.assertEqual(response.status_code, 400)