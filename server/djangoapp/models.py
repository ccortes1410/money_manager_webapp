from django.db import models
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
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES)
   
    class Meta:
        unique_together = ('name', 'user')

    def __str__(self):
        return f"Category: {self.name} by {self.user.username}"


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
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"Recurring Transaction {self.id}: {self.amount} every {self.frequency} starting {self.start_date} by {self.user.username}"