import os
import django
import sys

# Ensure the parent directory is in sys.path so djangoproj can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoproj.settings")
django.setup()

from djangoapp.models import Transactions

def initiate():
    # Sample data to populate the database
    sample_transactions = [
        {"user_id": 1, "amount": 100.00, "date": "2023-01-01", "description": "Grocery Shopping"},
        {"user_id": 2, "amount": 50.00, "date": "2023-01-02", "description": "Gas"},
        {"user_id": 3, "amount": 200.00, "date": "2023-01-03", "description": "Rent"},
    ]

    for transaction_data in sample_transactions:
        Transactions.objects.create(**transaction_data)