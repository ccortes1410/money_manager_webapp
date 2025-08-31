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
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES)

    class Meta:
        unique_together = ('name', 'user')

    def __str__(self):
        return f"Category: {self.category.name} by {self.user.username}"