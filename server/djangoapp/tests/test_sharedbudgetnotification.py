"""
Tests for the SharedBudgetNotification model and the
get_budget_notifications endpoint.
"""
from django.urls import reverse

from djangoapp.models.models import SharedBudgetNotification

from .test_base import BaseTestCase


class SharedBudgetNotificationModelTests(BaseTestCase):
    def test_create_notification_usual(self):
        notification = self.create_shared_budget_notification()
        self.assertFalse(notification.is_read)

    def test_str_representation(self):
        notification = self.create_shared_budget_notification()
        expected = f"{notification.notification_type} for {notification.user.username}"
        self.assertEqual(str(notification), expected)

    def test_mark_as_read(self):
        notification = self.create_shared_budget_notification()
        notification.mark_as_read()
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
    
    def test_shared_budget_can_be_null(self):
        notification = SharedBudgetNotification.objects.create(
            user=self.user1, from_user=self.user2, notification_type='budget_updated',
            message='General Update', shared_budget=None
        )
        self.assertIsNone(notification.shared_budget)

    def test_ordering_most_recent_first(self):
        budget = self.create_shared_budget()
        older = self.create_shared_budget_notification(shared_budget=budget)
        newer = SharedBudgetNotification.objects.create(
            user=self.user1, from_user=self.user2, notification_type='expense_added',
            shared_budget=budget, message='Newer'
        )
        notifications = list(SharedBudgetNotification.objects.filter(user=self.user1))
        self.assertEqual(notifications[0], newer)
        self.assertEqual(notifications[1], older)

    
class SharedBudgetNotificationAPITests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user1)

    def test_requires_auth(self):
        self.client.logout()
        response = self.client.get(reverse('djangoapp:get_budget_notifications'))
        self.assertEqual(response.status_code, 401)

    def test_returns_notifications_for_current_user_only(self):
        self.create_shared_budget_notification()
        SharedBudgetNotification.objects.create(
            user=self.user2, from_user=self.user1, notification_type='budget_updated', message='Not for user1'
        )
        response = self.client.get(reverse('djangoapp:get_budget_notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['notifications']), 1)

    def test_unread_only_filter(self):
        read_notification = self.create_shared_budget_notification()
        read_notification.mark_as_read()
        self.create_shared_budget_notification()

        response = self.client.get(reverse('djangoapp:get_budget_notifications'), {'unread_only': 'true'})
        data = response.json()
        self.assertEqual(len(data['notifications']), 1)
        self.assertEqual(data['unread_count'], 1)