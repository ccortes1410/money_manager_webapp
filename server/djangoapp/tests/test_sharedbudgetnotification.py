"""
Tests for the SharedBudgetNotification model and the
get_budget_notifications endpoint.
"""
import json
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone

from djangoapp.models.models import SharedBudgetNotification
from .test_base import BaseTestCase
from .test_api_backend import TestApiBackend


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
        self.test_api = TestApiBackend()
        for verb in ("get", "post", "patch", "delete"):
            patcher = patch(
                f"djangoapp.restapi.requests.{verb}",
                side_effect=getattr(self.test_api, verb),
            )
            patcher.start()
            self.addCleanup(patcher.stop)

    def _seed_user(self, user_id, username=None):
        if username is None:
            username = f'user{user_id}'
        row = {
            "id": user_id,
            "username": username,
            "email": f'{username}@example.com',
            "first_name": '',
            "last_name": '',
        }
        return self.test_api.seed("users", row)

    def _seed_shared_budget(self, **overrides):
        row = {
            "name": "Test Budget",
            "description": "Test budget description",
            "total_amount": "1000.00",
            "category": "General",
            "created_by": self.user1.id,
            "period_start": self.today.isoformat(),
            "period_end": (self.today + timezone.timedelta(days=30)).isoformat(),
            "is_active": True,
            "default_split_type": "equal",
        }
        row.update(overrides)
        return self.test_api.seed("shared-budgets", row)

    def test_requires_auth(self):
        self.client.logout()
        response = self.client.get(reverse('djangoapp:get_budget_notifications'))
        self.assertEqual(response.status_code, 401)

    def test_returns_notifications_for_current_user_only(self):
        # Seed users
        self._seed_user(self.user1.id)
        self._seed_user(self.user2.id)

        # Seed notification for user1
        self.test_api.seed("shared-budget-notifications", {
            "id": 1,
            "user_id": self.user1.id,
            "from_user_id": self.user2.id,
            "notification_type": "budget_updated",
            "message": "For user1",
            "is_read": False,
        })

        # Seed notification for user2
        self.test_api.seed("shared-budget-notifications", {
            "id": 2,
            "user_id": self.user2.id,
            "from_user_id": self.user1.id,
            "notification_type": "budget_updated",
            "message": "Not for user1",
            "is_read": False,
        })

        response = self.client.get(reverse('djangoapp:get_budget_notifications'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['notifications']), 1)
        self.assertEqual(data['notifications'][0]['message'], "For user1")

    def test_unread_only_filter(self):
        # Seed user
        self._seed_user(self.user1.id)

        # Seed read notification
        read_notification = self.test_api.seed("shared-budget-notifications", {
            "id": 1,
            "user_id": self.user1.id,
            "from_user_id": self.user2.id,
            "notification_type": "budget_updated",
            "message": "Read notification",
            "is_read": True,
        })

        # Seed unread notification
        unread_notification = self.test_api.seed("shared-budget-notifications", {
            "id": 2,
            "user_id": self.user1.id,
            "from_user_id": self.user2.id,
            "notification_type": "expense_added",
            "message": "Unread notification",
            "is_read": False,
        })

        response = self.client.get(reverse('djangoapp:get_budget_notifications'), {'unread_only': 'true'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['notifications']), 1)
        self.assertEqual(data['notifications'][0]['message'], "Unread notification")
        self.assertEqual(data['unread_count'], 1)