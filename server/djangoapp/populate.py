import os
import django
import sys

# Ensure the parent directory is in sys.path so djangoproj can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoproj.settings")
django.setup()

from django.contrib.auth.models import User
from djangoapp.models import Transaction

def initiate():
    # Create users
    Krlp, _ = User.objects.get_or_create(username='Krlp', defaults={'password': 'Ralco2011'})    
    user1, _ = User.objects.get_or_create(username='user1', defaults={'password': 'password1'})
    user2, _ = User.objects.get_or_create(username='user2', defaults={'password': 'password2'})
    user3, _ = User.objects.get_or_create(username='user3', defaults={'password': 'password3'})

    # Sample data to populate the database
    sample_transactions = [
        {"user": Krlp, "amount": 100.00, "date": "2023-01-01", "description": "Grocery Shopping", "category": "Food"},
        {"user": user1, "amount": 50.00, "date": "2023-01-02", "description": "Gas", "category": "Transport"},
        {"user": Krlp, "amount": 200.00, "date": "2023-01-03", "description": "Rent", "category": "Housing"},
        {"user": Krlp, "amount": 150.00, "date": "2023-01-04", "description": "Utilities", "category": "Housing"},
        {"user": user2, "amount": 75.00, "date": "2023-01-05", "description": "Dining Out", "category": "Food"},
        {"user": user3, "amount": 300.00, "date": "2023-01-06", "description": "Gym Membership", "category": "Health"},
        {"user": user1, "amount": 400.00, "date": "2023-01-07", "description": "Online Shopping", "category": "Entertainment"}
    ]

    for transaction_data in sample_transactions:
        Transaction.objects.create(**transaction_data)

    

if __name__ == "__main__":
    initiate()