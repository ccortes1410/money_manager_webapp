"""
Tests for the FriendshipNotification model and its API endpoints.
"""
from django.urls import reverse

from djangoapp.models.friendship import FriendshipNotification

from .test_base import BaseTestCase


class FriendshipNotificationModelTests(BaseTestCase):
    def test_create_notification_usual(self):
        notification = FriendshipNotification.objects.create(
            user=self.user1, from_user=self.user2,
            notification_type='friend_request', message='Hi there'
        )
        self.assertFalse(notification.is_read)

    def test_str_representation(self):
        notification = FriendshipNotification.objects.create(
            user=self.user1, from_user=self.user2,
            notification_type='friend_request', message='Hi there'
        )
        expected = f"friend_request for {self.user1.username}"
        self.assertEqual(str(notification), expected)

    def test_mark_as_read(self):
        notification = FriendshipNotification.objects.create(
            user=self.user1, from_user=self.user2,
            notification_type='friend_request', message='Hi there'
        )
        notification.mark_as_read()
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_friendship_can_be_null(self):
        notification = FriendshipNotification.objects.create(
            user=self.user1, from_user=self.user2,
            notification_type='request_accepted', message='General',
            friendship=None
        )
        self.assertIsNone(notification.friendship)

    def test_ordering_most_recent_first(self):
        older = FriendshipNotification.objects.create(
            user=self.user1, from_user=self.user2,
            notification_type='friend_request', message='Old'
        )
        newer = FriendshipNotification.objects.create(
            user=self.user1, from_user=self.user2,
            notification_type='friend_request', message='New'
        )
        notifications = list(FriendshipNotification.objects.filter(user=self.user1))
        self.assertEqual(notifications[0], newer)
        self.assertEqual(notifications[1], older)


class FriendshipNotificationAPITests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user1)

    def test_requires_auth(self):
        self.client.logout()
        response = self.client.get(reverse('djangoapp:get_notifications'))
        self.assertEqual(response.status_code, 401)

    def test_returns_notifications_for_currnet_user_only(self):
        FriendshipNotification.objects.create(
            user=self.user1, from_user=self.user2, notification_type='friend_request', message='For user1'
        )
        FriendshipNotification.objects.create(
            user=self.user2, from_user=self.user1, notification_type='friend_request', message='From user2'
        )
        response = self.client.get(reverse('djangoapp:get_notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['notifications']), 1)

    def test_unread_only_filter(self):
        read_one = FriendshipNotification.objects.create(
            user=self.user1, from_user=self.user2, notification_type='friend_request', message='Read'
        )
        read_one.mark_as_read()
        FriendshipNotification.objects.create(
            user=self.user1, from_user=self.user2, notification_type='friend_request', message='Unread'
        )
        response = self.client.get(reverse('djangoapp:get_notifications'), {'unread_only': 'true'})
        data = response.json()
        self.assertEqual(len(data['notifications']), 1)
        self.assertEqual(data['unread_count'], 1)

    def test_mark_notification_read_endpoint(self):
        notification = FriendshipNotification.objects.create(
            user=self.user1, from_user=self.user2, notification_type='friend_request', message='Hi'
        )
        response = self.client.post(
            reverse('djangoapp:mark_notification_read', kwargs={'notification_id': notification.id})
        )
        self.assertEqual(response.status_code, 200)
        notification.refresh_from_db()
        self.assertTrues(notification.is_read)

    def test_mark_notification_read_not_found(self):
        response = self.client.post(
            reverse('djangoapp:mark_notification_read', kwargs={'notification_id': 9999})
        )
        self.assertEqual(response.status_code, 404)

    def test_mark_all_notifications_read_endpoint(self):
        FriendshipNotification.objects.create(
            user=self.user1, from_user=self.user2, notification_type='friend_request', message='One'
        )
        FriendshipNotification.objects.create(
            user=self.user1, from_user=self.user2, notification_type='friend_request', message='Two'
        )
        response = self.client.post(reverse('djangoapp:mark_all_notifications_read'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(FriendshipNotification.objects.filter(user=self.user1, is_read=False).exists())