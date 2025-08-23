from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Transaction(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    date = models.DateField()
    description = models.CharField(max_length=255)

    def __str__(self):
        return f"Transaction {self.id}: {self.amount} on {self.date} by {self.user.username}"