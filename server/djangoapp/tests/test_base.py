from django.test import TestCase
from django.contib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from djangoapp.models.models import (
    Transaction, Budget, Subscription, SubscriptionPayment,
    Income, SharedBudget, SharedBudgetMember, SharedBudgetInvite,
    SharedBudgetNotification, SharedExpense, ExpenseSplit, Settlement
)
from djangoapp.models.friendship import FriendshipNotification, Friendship

class BaseTestCase(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(username='user1', password='password1')
        self.user2 = User.objects.create_user(username='user2', password='password2')
        self.user3 = User.objects.create_user(username='user3', password='password3')

        self.today = timezone.now().date()

    def create_transaction(self):
        """Helper to create a Transacion with default values."""
        
        default_values = {
            'user': self.user1,
            'amount': Decimal('100'),
            'description': 'Test Transaction',
            'category': 'General',
            'date': self.today,
        }

        return Transaction.objects.create(
            **default_values
        )
    
    def create_budget(self):
        """Helper to create a Budget with defult values."""

        default_values = {
            'user': self.user1,
            'category': 'Entertainment',
            'amount': Decimal('1000'),
            'period_start': self.today,
            'period_end': self.today + timezone.timedelta(days=30),
            'recurrence': 'monthly',
            'is_active': True,
            'is_recurring': True,
            'is_shared': False,
        }

        return Budget.objects.create(
            **default_values
        )
    
    def create_subscription(self):
        """Helper to create a Subscription with default values."""

        default_values = {
            'user': self.user1,
            'name': 'Netflix',
            'amount': Decimal('9990'),
            'category': 'Entertainment',
            'billing_cycle': 'monthly',
            'billing_day': self.today.day,
            'start_date': self.today,
            'end_date': self.today + timezone.timedelta(days=30),
            'status': 'active',
            # 'description': 'Streaming service subscription',
        }

        return Subscription.objects.create(
            **default_values
        )
    
    def create_subscription_payment(self, subscription=None):
        """Helper to create a SubscriptionPayment with default values."""

        if subscription is None:
            subscription = self.create_subscription()

        default_values = {
            'subscription': subscription,
            'amount': subscription.amount,
            'is_paid': False,
            'paid_date': None,
        }

        return SubscriptionPayment.objects.create(
            **default_values
        )
    
    def create_income(self):
        """Helper to create an Income with default values."""
        
        first_of_month = self.today.replace(day=1)
        last_of_month = self.today.replace(day=28) + timezone.timedelta(days=4)

        default_values = {
            'user': self.user1,
            'amount': Decimal('5000'),
            'source': 'Salary',
            'date': self.today,
            'period_start': first_of_month,
            'period_end': last_of_month,
        }

        return Income.objects.create(
            **default_values
        )
    
    def create_shared_budget(self):
        """Helper to create a SharedBudget with default values."""

        default_values = {
            'name': 'Rent',
            'description': 'This is a shared budget for testing purposes.',
            'total_amount': Decimal('276914'),
            'category': 'General',
            'created_by': self.user1,
            'updated_at': timezone.now(),
            'period_start': self.today,
            'period_end': self.today + timezone.timedelta(days=30),
            'is_active': True,
            'default_split_type': 'equal'
        }

        return SharedBudget.objects.create(
            **default_values
        )
    
    def create_shared_budget_member(self, shared_budget=None, user=None):
        """Helper to create a SharedBudgetMember with default values."""

        if shared_budget is None:
            shared_budget = self.create_shared_budget()

        if user is None:
            user = self.user2

        default_values = {
            'shared_budget': shared_budget,
            'user': user,
            'role': 'owner',
            'contribution_percentage': Decimal('50'),
        }

        return SharedBudgetMember.objects.create(
            **default_values
        )
    
    def create_shared_budget_invite(self, shared_budget=None, invited_user=None):
        """Helper to create a SharedBudgetInvite with default values."""

        if shared_budget is None:
            shared_budget = self.create_shared_budget()

        if invited_user is None:
            invited_user = self.user3

        default_values = {
            'shared_budget': shared_budget,
            'invited_by': self.user1,
            'invited_user': self.user2,
            'role': 'editor',
            'status': 'pending',
            'message': 'You are invited to join the shared budget.',
        }

        return SharedBudgetInvite.objects.create(
            **default_values
        )
    
    def create_shared_expense(self, shared_budget=None):
        """Helper to create a SharedExpense with default values."""

        if shared_budget is None:
            shared_budget = self.create_shared_budget()

        default_values = {
            'shared_budget': shared_budget,
            'description': 'Test Shared Expense',
            'amount': Decimal('10000'),
            'paid_by': self.user1,
            'date': self.today,
            'category': 'General',
            'created_by': self.user1,
        }

        return SharedExpense.objects.create(
            **default_values
        )

    def create_expense_split(self, shared_expense=None, user=None): 
        """Helper to create an ExpenseSplit with default values."""

        if shared_expense is None:
            shared_expense = self.create_shared_expense()

        if user is None:
            user = self.user2

        default_values = {
            'shared_expense': shared_expense,
            'user': user,
            'amount_owed': Decimal('70000'),
            'is_settled': False,
        }

        return ExpenseSplit.objects.create(
            **default_values
        )
    
    def create_settlement(self, expense_split=None):
        """Helper to create a Settlement with default values."""

        if expense_split is None:
            expense_split = self.create_expense_split()

        default_values = {
            'shared_budget': expense_split.shared_expense.shared_budget,
            'payer': self.user1,
            'receiver': self.user2,
            'amount': expense_split.amount_owed,
            'date': self.today,
            'settled_at': timezone.now(),
        }

        return Settlement.objects.create(
            **default_values
        )
    
    def create_shared_budget_notification(self, shared_budget=None, user=None):
        """Helper to create a SharedBudgetNotification with default values."""

        if shared_budget is None:
            shared_budget = self.create_shared_budget()

        if user is None:
            user = self.user2

        default_values = {
            'user': self.user1,
            'from_user': self.user2,
            'notification_type': 'budget_invite',
            'shared_budget': shared_budget,
            'message': 'This is a notification for the shared budget.',
            'is_read': False,
        }

        return SharedBudgetNotification.objects.create(
            **default_values
        )