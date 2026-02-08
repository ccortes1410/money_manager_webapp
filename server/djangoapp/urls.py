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
from . import views

app_name = "djangoapp"
urlpatterns = [
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
    path(
        route='dashboard',
        view=views.dashboard,
        name='dashboard'
    ),
    path(
        route='transactions',
        view=views.transaction_list,
        name='transactions'
    ),
    path(
        route='transactions/delete',
        view=views.transaction_list,
        name='delete_transactions'
    ),
    path(
        route='budgets',
        view=views.get_budgets,
        name='budget_list'
    ),
    path(
        route='budget/<int:budget_id>',
        view=views.get_budget,
        name='budget_detail'
    ),
    path(
        route='budgets/create',
        view=views.budget_create,
        name='add_budget'
    ),
    path(
        route='budgets/<int:budget_id>/delete/',
        view=views.budget_delete,
        name='delete_budget'
    ),
    path(
        route='budgets/<int:budget_id>/update',
        view=views.update_budget_view,
        name='update_budget'
    ),
    path(
        route='budgets/<int:budget_id>/toggle-recurring',
        view=views.toggle_recurring,
        name='toggle_budget_recurring'
    ),
    path(
        route='subscriptions',
        view=views.subscriptions_list,
        name='subscriptions'
    ),
    path(
        route='subscriptions/create',
        view=views.subscriptions_create,
        name='subscriptions_create'
    ),
    path(
        route='subscriptions/<int:subscription_id>',
        view=views.subscriptions_detail,
        name='subscription_detail'
    ),
    path(
        route='subscriptions/<int:subscription_id>/delete',
        view=views.subscription_delete,
        name='subscription_delete'
    ),
    path(
        route='subscriptions/<int:subscription_id>/update',
        view=views.subscription_update,
        name='subcsription_update'
    ),
    path(
        route='subscriptions/<int:subscription_id>/status',
        view=views.subscription_update_status,
        name='subscription_status'
    ),
    path(
        route='payments/<int:payment_id>/toggle',
        view=views.payment_toggle_paid,
        name='payment_toggle'
    ),
    path(
        route='incomes',
        view=views.get_incomes,
        name='get_incomes'
    ),
    path(
        route='incomes/<int:income_id>',
        view=views.get_income,
        name='get_income'
    ),
    path(
        route='incomes/create',
        view=views.income_create,
        name='income_create'
    ),
    path(
        route='incomes/delete',
        view=views.income_delete,
        name='income_delete'
    ),
    path(
        route='incomes/<int:income_id>/update',
        view=views.income_update,
        name='income_update'
    ),
    path(
        route='user',
        view=views.current_user,
        name='current_user'
    ),
]
