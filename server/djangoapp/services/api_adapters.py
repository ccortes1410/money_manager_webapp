"""
Converts raw JSON rows returned by the Node database API into typed
objects, so the existing pure business-logic functions (things like
get_subscription_amount_for_period, which do date arithmetic and Decimal
math) can keep working completely unchanged.

This is the seam between "data access over HTTP" and "business logic in
Django" for the gateway architecture: fetch raw rows -> adapt -> compute.
"""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace


def _parse_date(value):
    return date.fromisoformat(value) if value else None


def _parse_decimal(value):
    return Decimal(str(value)) if value is not None else Decimal("0")


def budget_from_row(row):
    return SimpleNamespace(
        id=row["id"],
        user_id=row["user_id"],
        category=row["category"],
        amount=_parse_decimal(row["amount"]),
        period_start=_parse_date(row["period_start"]),
        period_end=_parse_date(row["period_end"]),
        recurrence=row.get("recurrence"),
        is_active=bool(row["is_active"]),
        is_recurring=bool(row["is_recurring"]),
        is_shared=bool(row["is_shared"]),
    )


def transaction_from_row(row):
    return SimpleNamespace(
        id=row["id"],
        user_id=row["user_id"],
        amount=_parse_decimal(row["amount"]),
        description=row["description"],
        category=row.get("category"),
        date=_parse_date(row["date"]),
    )


def subscription_from_row(row):
    return SimpleNamespace(
        id=row["id"],
        user_id=row["user_id"],
        name=row["name"],
        amount=_parse_decimal(row["amount"]),
        category=row["category"],
        billing_cycle=row["billing_cycle"],
        billing_day=row["billing_day"],
        start_date=_parse_date(row["start_date"]),
        end_date=_parse_date(row.get("end_date")),
        status=row["status"],
        description=row["description"],
        created_at=_parse_date(row.get("created_at")),
        updated_at=_parse_date(row.get("updated_at")),
    )


def subscription_payment_from_row(row):
    return SimpleNamespace(
        id=row["id"],
        subscription_id=row["subscription_id"],
        amount=_parse_decimal(row["amount"]),
        due_date=_parse_date(row["due_date"]),
        is_paid=bool(row["is_paid"]),
        paid_date=_parse_date(row.get("paid_date")),
    )

def income_from_row(row):
    return SimpleNamespace(
        id=row["id"],
        user_id=row["user_id"],
        amount=_parse_decimal(row["amount"]),
        source=row["source"],
        date_received=_parse_date(row["date_received"]),
        period_start=_parse_date(row["period_start"]),
        period_end=_parse_date(row["period_end"]),
    )


def shared_budget_from_row(row):
    return SimpleNamespace(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        total_amount=_parse_decimal(row["total_amount"]),
        category=row["category"],
        period_start=_parse_date(row["period_start"]),
        period_end=_parse_date(row["period_end"]),
        is_active=bool(row["is_active"]),
        default_split_type=row["default_split_type"],
        created_by=row["created_by"],
    )


def shared_budget_member_from_row(row):
    return SimpleNamespace(
        id=row["id"],
        shared_budget_id=row["shared_budget"],
        user_id=row["user_id"],
        role=row["role"],
        contriution_percentage=_parse_decimal(row["contribution_percentage"]),
        joined_at=_parse_date(row.get("joined_at")),
    )


def shared_budget_invite_from_row(row):
    return SimpleNamespace(
        id=row["id"],
        shared_budget_id=row["shared_budget"],
        invited_by_id=row["invited_by"],
        invited_user_id=row["invited_user"],
        role=row["role"],
        message=row["message"],
        status=row["status"],
        created_at=_parse_date(row.get("created_at")),
    )


def shared_expense_from_row(row):
    return SimpleNamespace(
        id=row["id"],
        shared_budget_id=row["shared_budget"],
        description=row["description"],
        amount=_parse_decimal(row["amount"]),
        paid_by_id=row["paid_by"],
        date=_parse_date(row["date"]),
        category=row["category"],
        created_by_id=row["created_by"],
        notes=row["notes"],
    )


def expense_split_from_row(row):
    return SimpleNamespace(
        id=row["id"],
        shared_expense_id=row["shared_expense"],
        user_id=row["user_id"],
        amount_owed=_parse_decimal(row["amount_owed"]),
        is_settled=bool(row["is_settled"]),
        settled_at=_parse_date(row.get("settled_at")),
    )


def settlement_from_row(row):
    return SimpleNamespace(
        id=row["id"],
        shared_budget_id=row["shared_budget"],
        payer_id=row["payer"],
        receiver_id=row["receiver"],
        amount=_parse_decimal(row["amount"]),
        date=_parse_date(row["date"]),
        notes=row["notes"],
        created_at=_parse_date(row.get("created_at")),
    )


def shared_budget_notification_from_row(row):
    return SimpleNamespace(
        id=row["id"],
        user_id=row["user_id"],
        from_user_id=row["from_user"],
        notification_type=row["notification_type"],
        shared_budget_id=row["shared_budget"],
        message=row["message"],
        is_read=bool(row["is_read"]),
        created_at=_parse_date(row.get("created_at")),
    )
