from django.contrib import admin
from .models import Budget, Transaction

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'amount', 'date', 'description')
    search_fields = ('description',)

class BudgetAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'amount', 'period')
    search_fields = ('name',)

admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Budget, BudgetAdmin)