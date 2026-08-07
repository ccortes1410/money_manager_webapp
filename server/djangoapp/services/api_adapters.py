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
    )