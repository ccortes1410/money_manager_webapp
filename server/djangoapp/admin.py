from django.contrib import admin
from .models import Transactions

class TransactionsAdmin(admin.ModelAdmin):
    list_display = ('id', 'amount', 'date', 'description')
    search_fields = ('description',)

admin.site.register(Transactions, TransactionsAdmin)