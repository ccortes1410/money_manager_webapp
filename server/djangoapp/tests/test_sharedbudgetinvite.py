"""
Tests for the SharedBudgetInvite model and its API endpoints.
"""
import json
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone

from djangoapp.models.models import SharedBudgetInvite, SharedBudgetMember
from djangoapp.models.friendship import Friendship

from .test_base import BaseTestCase
from .test_api_backend import TestApiBackend
from django.utils import timezone


class SharedBudgetInviteModelTests(BaseTestCase):
    def test_create_invite_usual(self):
        invite = self.create_shared_budget_invite()
        self.assertEqual(invite.status, 'pending')

    def test_str_representation(self):
        invite = self.create_shared_budget_invite()
        expected = f"Invite: {invite.invited_user.username} to {invite.shared_budget.name}"
        self.assertEqual(str(invite), expected)

    def test_unique_together_budget_and_invited_user(self):
        from django.db import IntegrityError, transaction
        budget = self.create_shared_budget()
        SharedBudgetInvite.objects.create(
            shared_budget=budget, invited_by=self.user1, invited_user=self.user2, role='editor'
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SharedBudgetInvite.objects.create(
                    shared_budget=budget, invited_by=self.user1, invited_user=self.user2, role='editor'
                )

    def test_accept_creates_member_and_updates_status(self):
        budget = self.create_shared_budget()
        invite = SharedBudgetInvite.objects.create(
            shared_budget=budget, invited_by=self.user1, invited_user=self.user2, role='editor'
        )
        invite.accept()
        invite.refresh_from_db()
        self.assertEqual(invite.status, 'accepted')
        self.assertIsNotNone(invite.responded_at)
        self.assertTrue(budget.is_member(self.user2))
        self.assertEqual(budget.get_member_role(self.user2), 'editor')

    def test_decline_updates_status_without_creating_member(self):
        budget = self.create_shared_budget()
        invite = SharedBudgetInvite.objects.create(
            shared_budget=budget, invited_by=self.user1, invited_user=self.user2, role='editor'
        )
        invite.decline()
        invite.refresh_from_db()
        self.assertEqual(invite.status, 'declined')
        self.assertFalse(budget.is_member(self.user2))


class SharedBudgetInviteAPITests(BaseTestCase):
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

    def _seed_shared_budget_member(self, shared_budget_id, user_id, role='owner'):
        row = {
            "shared_budget": shared_budget_id,
            "user_id": user_id,
            "role": role,
            "contribution_percentage": 100,
            "joined_at": self.today.isoformat(),
        }
        return self.test_api.seed("shared-budget-members", row)

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

    def test_invite_to_budget_requires_friendship(self):
        budget = self._seed_shared_budget()
        self._seed_shared_budget_member(budget["id"], self.user1.id, 'owner')
        self._seed_user(self.user2.id)

        response = self.client.post(
            reverse('djangoapp:invite_to_budget', kwargs={'budget_id': budget["id"]}),
            data=json.dumps({'user_id': self.user2.id}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_invite_to_budget_success_when_friends(self):
        budget = self._seed_shared_budget()
        self._seed_shared_budget_member(budget["id"], self.user1.id, 'owner')
        self._seed_user(self.user1.id)
        self._seed_user(self.user2.id)

        # Create friendships
        self.test_api.seed("friendships", {"sender": self.user1.id, "receiver": self.user2.id, "status": 'accepted'})

        response = self.client.post(
            reverse('djangoapp:invite_to_budget', kwargs={'budget_id': budget["id"]}),
            data=json.dumps({'user_id': self.user2.id}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

        # Check that invite was created in the mock API
        invites = self.test_api.resources["shared-budget-invites"]
        self.assertEqual(len(invites), 1)
        self.assertEqual(invites[0]["shared_budget"], budget["id"])
        self.assertEqual(invites[0]["invited_user"], self.user2.id)

    def test_invite_to_budget_requires_edit_permission(self):
        budget = self._seed_shared_budget()
        self._seed_shared_budget_member(budget["id"], self.user1.id, 'owner')
        self._seed_user(self.user1.id)
        self._seed_user(self.user2.id)
        self._seed_user(self.user3.id)

        # Create friendship between user 2 and user3 (not involving the budget owner)
        self.test_api.seed("friendships", {"sender": self.user2.id, "receiver": self.user3.id, "status": 'accepted'})
        self.client.force_login(self.user2) # not owner/editor of the budget

        response = self.client.post(
            reverse('djangoapp:invite_to_budget', kwargs={'budget_id': budget["id"]}),
            data=json.dumps({'user_id': self.user3.id}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_respond_accept_creates_member_and_updates_status(self):
        budget = self._seed_shared_budget()
        self._seed_shared_budget_member(budget["id"], self.user1.id, 'owner')
        self._seed_user(self.user1.id)
        self._seed_user(self.user2.id)

        # Create invite via API
        invite_row = self.test_api.seed("shared-budget-invites", {
            'shared_budget': budget["id"],
            'invited_by': self.user1.id,
            'invited_user': self.user2.id,
            'role': 'editor',
            'message': 'Test invite',
            'status': 'pending'
        })

        self.client.force_login(self.user2)

        response = self.client.post(
            reverse('djangoapp:respond_to_budget_invite', kwargs={'invite_id': invite_row["id"]}),
            data=json.dumps({'action': 'accept'}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Check that invite status was updated
        invite_row = self.test_api.resources["shared-budget-invites"][0]
        self.assertEqual(invite_row["status"], 'accepted')

        # Check that member was created
        members = self.test_api.resources["shared-budget-members"]
        self.assertEqual(len(members), 2) # Owner + new member
        member = [m for m in members if m["user_id"] == self.user2.id][0]
        self.assertEqual(member["role"], 'editor')
        self.assertEqual(member["shared_budget"], budget["id"])

    def test_respond_decline_succeeds(self):
        budget = self._seed_shared_budget()
        self._seed_shared_budget_member(budget["id"], self.user1.id, 'owner')
        self._seed_user(self.user1.id)
        self._seed_user(self.user2.id)

        # Create invite via API
        invite_row = self.test_api.seed("shared-budget-invites", {
            'shared_budget': budget["id"],
            'invited_by': self.user1.id,
            'invited_user': self.user2.id,
            'role': 'editor',
            'message': 'Test invite',
            'status': 'pending'
        })

        self.client.force_login(self.user2)
        response = self.client.post(
            reverse('djangoapp:respond_to_budget_invite', kwargs={'invite_id': invite_row["id"]}),
            data=json.dumps({'action': 'decline'}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Check that invite status was updated
        invite_row = self.test_api.resources["shared-budget-invites"][0]
        self.assertEqual(invite_row["status"], 'declined')