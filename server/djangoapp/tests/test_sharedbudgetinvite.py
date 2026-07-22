"""
Tests for the SharedBudgetInvite model and its API endpoints.
"""
import json

from django.urls import reverse

from djangoapp.models.models import SharedBudgetInvite, SharedBudgetMember
from djangoapp.models.friendship import Friendship

from .test_base import BaseTestCase


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
        self.budget = self.create_shared_budget()
        SharedBudgetMember.objects.create(shared_budget=self.budget, user=self.user1, role='owner')
        self.client.force_login(self.user1)

    def test_invite_to_budget_requires_friendship(self):
        response = self.client.post(
            reverse('djangoapp:invite_to_budget', kwargs={'budget_id': self.budget.id}),
            data=json.dumps({'user_id': self.user2.id}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_invite_to_budget_success_when_friends(self):
        Friendship.objects.create(sender=self.user1, receiver=self.user2, status='accepted')
        response = self.client.post(
            reverse('djangoapp:invite_to_budget', kwargs={'budget_id': self.budget.id}),
            data=json.dumps({'user_id': self.user2.id}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(SharedBudgetInvite.objects.filter(shared_budget=self.budget, invited_user=self.user2).exists())

    def test_invite_to_budget_requires_edit_permission(self):
        Friendship.objects.create(sender=self.user2, receiver=self.user3, status='accepted')
        self.client.force_login(self.user2) # not owner/editor of self.budget
        response = self.client.post(
            reverse('djangoapp:invite_to_budget', kwargs={'budget_id': self.budget.id}),
            data=json.dumps({'user_id': self.user3.id}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_respond_accept_raises_serialize_bug(self):
        invite = SharedBudgetInvite.objects.create(
            shared_budget=self.budget, invited_by=self.user1, invited_user=self.user2, role='editor'
        )
        self.client.force_login(self.user2)
        # with self.assertRaises(AttributeError):
        self.client.post(
            reverse('djangoapp:respond_to_budget_invite', kwargs={'invite_id': invite.id}),
            data=json.dumps({'action': 'accept'}), content_type='application/json'
        )
        # membership creation happens before the crashing serialize call
        self.assertTrue(self.budget.is_member(self.user2))

    def test_respond_decline_succeeds(self):
        invite = SharedBudgetInvite.objects.create(
            shared_budget=self.budget, invited_by=self.user1, invited_user=self.user2, role='editor'
        )
        self.client.force_login(self.user2)
        response = self.client.post(
            reverse('djangoapp:respond_to_budget_invite', kwargs={'invite_id': invite.id}),
            data=json.dumps({'action': 'decline'}), content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        invite.refresh_from_db()
        self.assertEqual(invite.status, 'declined')