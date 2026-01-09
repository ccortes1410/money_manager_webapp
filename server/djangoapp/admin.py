from django.contrib import admin
from .models import Budget, Transaction, Subscription

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'amount', 'date', 'description')
    search_fields = ('description',)

class BudgetAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'category', 'amount', 'period')
    search_fields = ('category',)

class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'category', 'amount', 'is_active')
    search_fields = ('category',)

class IncomeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'source', 'date_received')
    search_fields = ('source',)

admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Budget, BudgetAdmin)
admin.site.register(Subscription, SubscriptionAdmin)