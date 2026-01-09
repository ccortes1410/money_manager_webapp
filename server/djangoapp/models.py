from django.db import models
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
    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly')
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    category = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    reset_day = models.PositiveSmallIntegerField(
        default=1,
        help_text="Day of the month when the budget resets (1-31)"
    )
    expires_at = models.DateField(blank=True, null=True)
   
    class Meta:
        unique_together = ('category', 'user')

    def __str__(self):
        return f"Category: {self.name} by {self.user.username}"
    
    @property
    def is_expired(self):
        if self.expires_at and timezone.now().date() > self.expires_at:
            return True
        return False
    
    @property
    def next_reset_date(self):
        """ Compute next reset day based on current month and reset_day. """
        from datetime import date, timedelta
        import calendar
        today = timezone.now().date()
        _, days_in_month = calendar.monthrange(today.year, today.month)
        reset_day = min(self.reset_day, days_in_month)
        reset_date = date(today.year, today.month, reset_day)
        if reset_date <= today:
            # move to next month
            month = 1 if today.month == 12 else today.month + 1
            year = today.year + 1 if today.month == 12 else today.year
            _, days_in_next = calendar.monthrange(year, month)
            reset_day = min(self.reset_day, days_in_next)
            reset_date = date(year, month, reset_day)
        return reset_date


class Subscription(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    category = models.CharField(max_length=100, null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    due_date = models.DateField()
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Recurring Transaction {self.id}: {self.amount} every {self.frequency} starting {self.start_date} by {self.user.username}"
    
class Income(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    source = models.CharField(max_length=255)
    date_received = models.DateField()
    date_intended = models.DateField()

    def __str__(self):
        return f"Income {self.id}: {self.amount} from {self.source} on {self.date_received} by {self.user.username}"