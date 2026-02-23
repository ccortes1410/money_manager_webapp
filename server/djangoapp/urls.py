"""
URL configuration for money_manager_webapp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.conf import settings
from .views import (
    views,
    dashboard_views,
    transactions_views,
    budgets_views,
    subscriptions_views,
    incomes_views,
    friendship_views,
    shared_budget_views,   
)

app_name = "djangoapp"
urlpatterns = [
    # Authentication
    path(
        route='register',
        view=views.register_user,
        name='register'
    ),
    path(
        route='login',
        view=views.login_request,
        name='login'
    ),
    path(
        route='logout',
        view=views.logout_request,
        name='logout'
    ),

    # Dashboard
    path(
        route='dashboard',
        view=dashboard_views.dashboard,
        name='dashboard'
    ),

    # Transactions
    path(
        route='transactions',
        view=transactions_views.get_transactions,
        name='transactions'
    ),
    path(
        route='transactions/create',
        view=transactions_views.transaction_create,
        name='transaction_create'
    ),
    path(
        route='transactions/<int:transaction_id>/update',
        view=transactions_views.transaction_update,
        name='transaction_update'
    ),
    path(
        route='transactions/delete',
        view=transactions_views.transaction_delete,
        name='transaction_delete'
    ),

    # Budgets
    path(
        route='budgets',
        view=budgets_views.get_budgets,
        name='budget_list'
    ),
    path(
        route='budget/<int:budget_id>',
        view=budgets_views.get_budget,
        name='budget_detail'
    ),
    path(
        route='budgets/create',
        view=budgets_views.budget_create,
        name='add_budget'
    ),
    path(
        route='budgets/<int:budget_id>/delete/',
        view=budgets_views.budget_delete,
        name='delete_budget'
    ),
    path(
        route='budgets/<int:budget_id>/update',
        view=budgets_views.update_budget_view,
        name='update_budget'
    ),
    path(
        route='budgets/<int:budget_id>/toggle-recurring',
        view=budgets_views.toggle_recurring,
        name='toggle_budget_recurring'
    ),

    # Subscriptions
    path(
        route='subscriptions',
        view=subscriptions_views.subscriptions_list,
        name='subscriptions'
    ),
    path(
        route='subscriptions/create',
        view=subscriptions_views.subscriptions_create,
        name='subscriptions_create'
    ),
    path(
        route='subscriptions/<int:subscription_id>',
        view=subscriptions_views.subscriptions_detail,
        name='subscription_detail'
    ),
    path(
        route='subscriptions/<int:subscription_id>/delete',
        view=subscriptions_views.subscription_delete,
        name='subscription_delete'
    ),
    path(
        route='subscriptions/<int:subscription_id>/update',
        view=subscriptions_views.subscription_update,
        name='subscription_update'
    ),
    path(
        route='subscriptions/<int:subscription_id>/status',
        view=subscriptions_views.subscription_update_status,
        name='subscription_status'
    ),
    path(
        route='payments/<int:payment_id>/toggle',
        view=subscriptions_views.payment_toggle_paid,
        name='payment_toggle'
    ),

    # Incomes
    path(
        route='incomes',
        view=incomes_views.get_incomes,
        name='get_incomes'
    ),
    path(
        route='incomes/<int:income_id>',
        view=incomes_views.get_income,
        name='get_income'
    ),
    path(
        route='incomes/create',
        view=incomes_views.income_create,
        name='income_create'
    ),
    path(
        route='incomes/delete',
        view=incomes_views.income_delete,
        name='income_delete'
    ),
    path(
        route='incomes/<int:income_id>/update',
        view=incomes_views.income_update,
        name='income_update'
    ),

    # Friends
    path(
        route='friends',
        view=friendship_views.get_friends,
        name='get_friends'
    ),
    path(
        route='friends/requests',
        view=friendship_views.get_pending_requests,
        name='get_pending_requests'
    ),
    path(
        route='friends/request',
        view=friendship_views.send_friend_request,
        name='send_friend_request'
    ),
    path(
        route='friends/request/<int:friendship_id>/respond',
        view=friendship_views.respond_to_request,
        name='respond_to_request'
    ),
    path(
        route='friends/request/<int:friendship_id>/cancel',
        view=friendship_views.cancel_request,
        name='cancel_request'
    ),
    path(
        route='friends/<int:friend_id>/remove',
        view=friendship_views.remove_friend,
        name='remove_friend'
    ),
    path(
        route='friends/search',
        view=friendship_views.search_users,
        name='search_users'
    ),

    # Shared Budgets
    path(
        route='shared-budgets',
        view=shared_budget_views.get_shared_budgets,
        name='get_shared_budgets'
    ),
    path(
        route='shared-budgets/create',
        view=shared_budget_views.create_shared_budget,
        name='create_shared_budget'
    ),
    path(
        route='shared-budgets/<int:budget_id>',
        view=shared_budget_views.get_shared_budget_detail,
        name='get_shared_budget_detail'
    ),
    path(
        route='shared-budgets/<int:budget_id>/update',
        view=shared_budget_views.update_shared_budget,
        name='update_shared_budget'
    ),
    path(
        route='shared-bugdets/<int:budget_id>/delete',
        view=shared_budget_views.delete_shared_budget,
        name='delete_shared_budget'
    ),

    # Shared Budget Invites
    path(
        route='shared-budgets/<int:budget_id>/invite',
        view=shared_budget_views.invite_to_budget,
        name='invite_to_budget'
    ),
    path(
        route='shared-budgets/invite/<int:invite_id>/respond',
        view=shared_budget_views.respond_to_budget_invite,
        name="respond_to_budget_invite"
    ),

    # Shared Budget Members
    path(
        route='shared-budgets/<int:budget_id>/members/<int:member_id>/role',
        view=shared_budget_views.update_member_role,
        name='update_member_role'
    ),
    path(
        route='shared-budgets/<int:budget_id>/members/<int:member_id>/remove',
        view=shared_budget_views.remove_member,
        name='remove_member'
    ),
    path(
        route='shared-budgets/<int:budget_id>/leave',
        view=shared_budget_views.leave_budget,
        name='leave_budget'
    ),

    # Shared Budget Expenses
    path(
        route='shared-budgets/<int:budget_id>/expenses',
        view=shared_budget_views.get_budget_expenses,
        name='get_budget_expenses'
    ),
    path(
        route='shared-budgets/<int:budget_id>/expenses/add',
        view=shared_budget_views.add_expense,
        name='add_expense'
    ),
    path(
        route='shared-budgets/<int:budget_id>/expenses/<int:expense_id>/update',
        view=shared_budget_views.update_expense,
        name='update_expense'
    ),
    path(
        route='shared-budgets/<int:budget_id>/expenses/<int:expense_id>/delete',
        view=shared_budget_views.delete_expense,
        name='delete_expense'
    ),

    # Settlements and Debts
    path(
        route='shared-budgets/<int:budget_id>/debts',
        view=shared_budget_views.get_budget_debts,
        name='get_budget_detbs'
    ),
    path(
        route='shared-budgets/<int:budget_id>/settle',
        view=shared_budget_views.create_settlement,
        name='create_settlement'
    ),

    # Budget Notifications
    path(
        route='budget-notifications',
        view=shared_budget_views.get_budget_notifications,
        name='get_budget_notifications'
    ),
    
    # Friend & Budget Notifications
    path(
        route='notifications', 
        view=friendship_views.get_notifications,
        name='get_notifications'
    ),
    path(
        route='notifications/<int:notification_id>/read',
        view=friendship_views.mark_notification_read,
        name='mark_notification_read'
    ),
    path(
        route='notifications/read-all',
        view=friendship_views.mark_all_notifications_read,
        name='mark_all_notifications_read'
    ),
    path(
        route='user',
        view=views.current_user,
        name='current_user'
    ),
    path(
        route='session',
        view=views.session_view,
        name='session'   
    ),
    path(
        route='logout',
        view=views.logout_view,
        name='logout'
    ),
]
