from django.contrib import admin
from .models import Budget, Transaction, Subscription, Income

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'amount', 'date', 'description')
    search_fields = ('description',)

class BudgetAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'category', 'amount', 'period_start', 'period_end', 'recurrence', 'is_active', 'is_recurring', 'is_shared', 'created_at')
    search_fields = ('category',)

class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'amount', 'category', 'billing_cycle', 'billing_day', 'start_date', 'end_date', 'status', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'category')

class IncomeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'source', 'date_received')
    search_fields = ('source',)

admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Budget, BudgetAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Income, IncomeAdmin)