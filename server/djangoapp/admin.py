from django.contrib import admin

from .models.models import (
    Transaction,
    Budget,
    Subscription,
    SubscriptionPayment,
    Income,
    SharedBudget,
    SharedBudgetMember,
    SharedBudgetInvite,
    SharedExpense,
    ExpenseSplit,
    Settlement,
    SharedBudgetNotification,
)
from .models.friendship import Friendship, FriendshipNotification


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'date', 'category', 'description')
    list_filter = ('category', 'date')
    search_fields = ('description', 'category', 'user__username')


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'category', 'amount', 'period_start', 'period_end',
        'recurrence', 'is_active', 'is_recurring', 'is_shared', 'created_at',
    )
    list_filter = ('is_active', 'is_recurring', 'is_shared', 'recurrence')
    search_fields = ('category', 'user__username')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'name', 'amount', 'category', 'billing_cycle',
        'billing_day', 'start_date', 'end_date', 'status', 'created_at', 'updated_at',
    )
    list_filter = ('status', 'billing_cycle')
    search_fields = ('name', 'category', 'user__username')


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'subscription', 'amount', 'due_date', 'is_paid', 'paid_date', 'created_at')
    list_filter = ('is_paid',)
    search_fields = ('subscription__name',)


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'source', 'date_received', 'period_start', 'period_end')
    search_fields = ('source', 'user__username')


@admin.register(SharedBudget)
class SharedBudgetAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'created_by', 'total_amount', 'category',
        'period_start', 'period_end', 'is_active', 'default_split_type', 'created_at'
    )
    list_filter = ('is_active', 'default_split_type')
    search_fields = ('name', 'category', 'created_by__username')


@admin.register(SharedBudgetMember)
class SharedBudgetMemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'shared_budget', 'user', 'role', 'contribution_percentage', 'joined_at')
    list_filter = ('role',)
    search_fields = ('shared_budget__name', 'user__username')


@admin.register(SharedBudgetInvite)
class SharedBudgetInviteAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'shared_budget', 'invited_by', 'invited_user', 'role',
        'status', 'created_at', 'responded_at'
    )
    list_filter = ('status', 'role')
    search_fields = ('shared_budget__name', 'invited_user__username', 'invited_by__username')


@admin.register(SharedExpense)
class SharedExpenseAdmin(admin.ModelAdmin):
    list_display = ('id', 'shared_budget', 'description', 'amount', 'paid_by', 'created_by', 'date', 'category')
    list_filter = ('category',)
    search_fields = ('description', 'shared_budget__name', 'paid_by__username')


@admin.register(ExpenseSplit)
class ExpenseSplitAdmin(admin.ModelAdmin):
    list_display = ('id', 'shared_expense', 'user', 'amount_owed', 'is_settled', 'settled_at')
    list_filter = ('is_settled',)
    search_fields = ('user__username', 'shared_expense_description')


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ('id', 'shared_budget', 'payer', 'receiver', 'amount', 'date', 'created_at')
    search_fields = ('shared_budget__name', 'payer__username', 'receiver__username')


@admin.register(SharedBudgetNotification)
class SharedBudgetNotification(admin.ModelAdmin):
    list_display = ('id', 'user', 'from_user', 'notification_type', 'shared_budget', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('message', 'user__username')


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'receiver', 'status', 'created_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('sender__username', 'receiver__username')


@admin.register(FriendshipNotification)
class FriendshipNotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'notification_type', 'friendship', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('message', 'user__username')