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
    period_start = models.DateField()
    period_end = models.DateField()

    def clean(self):
        if self.period_end < self.period_start:
            raise ValueError("End date must be after start date")
        
    def __str__(self):
        return f"Income {self.id}: {self.amount} from {self.source} on {self.date_received} by {self.user.username}"