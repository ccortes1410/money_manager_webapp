from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum, Q
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class Transaction(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    description = models.CharField(max_length=255)
    category = models.CharField(max_length=100, null=True, blank=True)
    date = models.DateField()

    
    def __str__(self):
        return f"Transaction {self.id}: {self.amount} on {self.date} by {self.user.username}"


class Budget(models.Model):
    RECURRENCE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly')
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)

    category = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    period_start = models.DateField()
    period_end = models.DateField()
    recurrence = models.CharField(
        max_length=10,
        choices=RECURRENCE_CHOICES,
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)
    is_recurring = models.BooleanField(default=True)
    is_shared = models.BooleanField(default=False)

    created_at = models.DateField(auto_now_add=True)
   
    class Meta:
        unique_together = ('category', 'user')
    
    def __str__(self):
        return f"Category: {self.category} by {self.user.username}"



class Subscription(models.Model):
    BILLING_CYCLE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled')
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    category = models.CharField(max_length=100)

    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES, default='monthly')
    billing_day = models.PositiveBigIntegerField(default=1, help_text="Day of month for monthly billing (1-31)")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - ${self.amount}/{self.billing_cycle}"


class SubscriptionPayment(models.Model):
    """ Records each individual payment/charge for a subscription."""

    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()

    is_paid = models.BooleanField(default=True)
    paid_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

        unique_together = ['subscription', 'date']

    def __str__(self):
        return f"{self.subscription.name} - ${self.amount} on {self.date}"
    

class Income(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    source = models.CharField(max_length=255)
    date_received = models.DateField()
    period_start = models.DateField()
    period_end = models.DateField()

    def clean(self):
        if self.period_end < self.period_start:
            raise ValueError("End date must be after start date")
        
    def __str__(self):
        return f"Income {self.id}: {self.amount} from {self.source} on {self.date_received} by {self.user.username}"
    

class SharedBudget(models.Model):
    """A budget shared between multiple users."""

    SPLIT_CHOICES = [
        ('equal', 'Equal Split'),
        ('percentage', 'By Percentage'),
        ('custom', 'Custom Amounts'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=12)
    category = models.CharField(max_length=50, blank=True, null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_shared_budgets'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    default_split_type = models.CharField(
        max_length=20,
        choices=SPLIT_CHOICES,
        default='equal'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} (${self.total_amount})"
    
    def get_total_spent(self):
        """Get total amount spent from this budget."""
        result = self.expenses.aggregate(total=Sum('amount'))
        return result['total'] or 0
    
    def get_remaining(self):
        """Get remaining budget amount."""
        return self.total_amount - self.get_total_spent()
    
    def get_progress_percentage(self):
        """Get percentage of budget spent."""
        if self.total_amount == 0:
            return 0
        return round((self.get_total_spent() / self.total_amount) * 100, 1)
    
    def get_member_count(self):
        """Get number of members of this budget."""
        return self.members.count()
    
    def get_members(self):
        """Get all members of this budget."""
        return [member.user for member in self.members.all()]
    
    def is_member(self, user):
        """Check if user is a member of this budget."""
        return self.members.filter(user=user).exists()
    
    def get_member_role(self, user):
        """Get a user's role in this budget."""
        member = self.members.filter(user=user).first()
        return member.role if member else None
    
    def can_edit(self, user):
        """Check if user can edit this budget."""
        member = self.members.filter(user=user).first()
        if not member:
            return False
        return member.role in ['owner', 'editor']
    
    def can_delete(self, user):
        """Check if user can delete this budget."""
        member = self.members.filter(user=user).first()
        if not member:
            return False
        return member.role == 'owner'
    

class SharedBudgetMember(models.Model):
    """Membership/participation in a shared budget."""

    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('editor', 'Editor'),
        ('viewer', 'Viewer'),
    ]

    shared_budget = models.ForeignKey(
        SharedBudget,
        on_delete=models.CASCADE,
        related_name='members'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shared_budget_memberships'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='editor')
    contribution_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['shared_budget', 'user']
        ordering = ['joined_at']

    def __str__(self):
        return f"{self.user.username} - {self.shared_budget.name} ({self.role})"
    
    def get_total_paid(self):
        """Get total amount this member has paid."""
        result = SharedExpense.objects.filter(
            shared_budget=self.shared_budget,
            paid_by=self.user
        ).aggregate(total=Sum('amount'))
        return result['total'] or 0
    
    def get_total_owed(self):
        """Get total amount this member owes (from splits)."""
        result = ExpenseSplit.objects.filter(
            expense__shared_budget=self.shared_budget,
            user=self.user,
            is_settled=False
        ).aggregate(total=Sum('amount_owed'))
        return result['total'] or 0
    
    def get_balance(self):
        """
        Get member's balance.
        Positive = others owe them, Negative = they owe others.
        """
        return self.get_total_paid() - self.get_total_owed()
    

class SharedBudgetInvite(models.Model):
    """Invitations to join a shared budget."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined')
    ]

    shared_budget = models.ForeignKey(
        SharedBudget,
        on_delete=models.CASCADE,
        related_name='invites'
    )
    invited_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_budget_invites'
    )
    invited_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_budget_invites'
    )
    role = models.CharField(
        max_length=20,
        choices=SharedBudgetMember.ROLE_CHOICES,
        default='editor'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ['shared_budget', 'invited_user']
        ordering = ['-created_at']

    def __str__(self):
        return f"Invite: {self.invited_user.username} to {self.shared_budget.name}"
    
    def accept(self):
        """Accept the invitation and add user to budget."""
        self.status = 'accepted'
        self.responded_at = timezone.now()
        self.save()

        # Add user as a member
        SharedBudgetMember.objects.create(
            shared_budget=self.shared_budget,
            user=self.invited_user,
            role=self.role
        )

    def decline(self):
        """Decline the invitation."""

        self.status = 'declined'
        self.responded_at = timezone.now()
        self.save()


class SharedExpense(models.Model):
    """An expense within a shared budget."""

    shared_budget = models.ForeignKey(
        SharedBudget,
        on_delete=models.CASCADE,
        related_name='expenses'
    )
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='paid_shared_expenses'
    )
    date = models.DateField()
    category = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_shared_expenses'
    )
    receipt_image = models.ImageField(upload_to='receipts/', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.description} - ${self.amount} by {self.paid_by.username}"
    
    def create_equal_split(self):
        """Create equal splits for all budget members."""
        members = self.shared_budget.members.all()
        member_count = members.count()

        if member_count == 0:
            return
        
        split_amount = self.amount / member_count

        for member in members:
            ExpenseSplit.objects.create(
                expense=self,
                user=member.user,
                amount_owed=split_amount
            )

    def create_percentage_splits(self):
        """Create splits based on member contribution percentages."""
        members = self.shared_budget.members.all()

        for member in members:
            split_amount = (self.amount * member.contribution_percentage) / 100
            ExpenseSplit.objects.create(
                expense=self,
                user=member.user,
                amount_owed=split_amount
            )

    def create_custom_splits(self, splits_data):
        """
        Create custom splits from provided data.
        splits_data = [{'user_id': 1, 'amount': 50.00}, ...]
        """

        for split in splits_data:
            user = User.objects.get(id=split['user_id'])
            ExpenseSplit.objects.create(
                expense=self,
                user=user,
                amount_owed=float(str(split['amount']))
            )


class ExpenseSplit(models.Model):
    """How an expense is split between members."""

    expense = models.ForeignKey(
        SharedExpense,
        on_delete=models.CASCADE,
        related_name='splits'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='expense_splits'
    )
    amount_owed = models.DecimalField(max_digits=12, decimal_places=2)
    is_settled = models.BooleanField(default=False)
    settled_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ['expense', 'user']
    
    def __str__(self):
        status = "Settled" if self.is_settled else "Pending"
        return f"{self.user.username} owes ${self.amount_owed} ({status})"
    
    def settle(self):
        """Mark this split as settled."""
        self.is_settled = True
        self.settled_at = timezone.now()
        self.save()


class Settlement(models.Model):
    """Track payments between users to settle debts."""
    
    shared_budget = models.ForeignKey(
        SharedBudget,
        on_delete=models.CASCADE,
        related_name='settlements'
    )
    payer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='settlements_paid'
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='settlements_received'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.payer.username} paid ${self.amount} to {self.receiver.username}"
    

class SharedBudgetNotification(models.Model):
    """Notifications for shared budget activities."""

    NOTIFICATION_TYPES = [
        ('budget_invite', 'Budget Invitation'),
        ('invite_accepted', 'Invitation Accepted'),
        ('invite_declined', 'Invitation Declined'),
        ('expense_added', 'Expense Added'),
        ('expense_updated', 'Expense Updated'),
        ('settlement_update', 'Settlement Made'),
        ('member_left', 'Member Left'),
        ('budget_updated', 'Budget Updated'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shared_budget_notifications'
    )
    from_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_budget_notifications'
    )
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    shared_budget = models.ForeignKey(
        SharedBudget,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type} for {self.user.username}"
    
    def mark_as_read(self):
        self.is_read=True
        self.save()