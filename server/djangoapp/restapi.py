import os
from datetime import date, datetime
from decimal import Decimal
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env.local', override=False)


def _resolve_backend_url():
    raw = (os.getenv('BACKEND_URL') or '').strip()
    local_defaults = ('http://api:3030/api/', 'http://localhost:3030/api/', 'http://127.0.0.1:3030/api/')

    # On Vercel, if no external BACKEND_URL is configured, return empty string so
    # restapi.py uses the direct TiDB ORM connection immediately with zero HTTP latency.
    if os.getenv('VERCEL') and (not raw or raw in local_defaults):
        return ''

    if not raw:
        raw = 'http://api:3030/api/'

    if not raw.endswith('/'):
        raw += '/'
    if not raw.endswith('/api/'):
        raw += 'api/'
    return raw


BACKEND_URL = _resolve_backend_url()
INTERNAL_API_KEY = os.getenv('INTERNAL_API_KEY') or os.getenv('DJANGO_SECRET_KEY', default="")
_BACKEND_UNREACHABLE = False


def _headers():
    return {"x-internal-api-key": INTERNAL_API_KEY}


def _log_request_error(method, url, e):
    detail = ""
    if hasattr(e, "response") and e.response is not None and getattr(e.response, "text", None):
        detail = f" - {e.response.text}"
    print(f"Error calling {method} {url}: {e}{detail}")


def _get_model_map():
    from django.contrib.auth.models import User
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

    return {
        "users": User,
        "transactions": Transaction,
        "budgets": Budget,
        "subscriptions": Subscription,
        "subscription-payments": SubscriptionPayment,
        "incomes": Income,
        "shared-budgets": SharedBudget,
        "shared-budget-members": SharedBudgetMember,
        "shared-budget-invites": SharedBudgetInvite,
        "shared-expenses": SharedExpense,
        "expense-splits": ExpenseSplit,
        "settlements": Settlement,
        "shared-budget-notifications": SharedBudgetNotification,
        "friendships": Friendship,
        "friendship-notifications": FriendshipNotification,
    }


def _serialize_instance(obj):
    from django.contrib.auth.models import User

    if isinstance(obj, User):
        return {
            "id": obj.id,
            "username": obj.username,
            "email": obj.email or "",
            "first_name": obj.first_name or "",
            "last_name": obj.last_name or "",
            "is_active": obj.is_active,
        }

    data = {}
    for field in obj._meta.concrete_fields:
        val = getattr(obj, field.attname)
        if isinstance(val, datetime):
            val = val.isoformat()
        elif isinstance(val, date):
            val = val.isoformat()
        elif isinstance(val, Decimal):
            val = str(val)
        data[field.attname] = val
        if field.name != field.attname and field.name not in data:
            data[field.name] = val
    return data


def _normalize_orm_field_and_value(model, key, value):
    from django.db import models as dj_models

    field_map = {f.name: f for f in model._meta.concrete_fields}
    attname_map = {f.attname: f for f in model._meta.concrete_fields}

    field = attname_map.get(key) or field_map.get(key)
    if not field and key.endswith("_id") and key[:-3] in field_map:
        field = field_map[key[:-3]]

    if not field:
        return None, None

    target_key = field.attname if isinstance(field, dj_models.ForeignKey) else field.name

    if value in ("true", "True") and isinstance(field, dj_models.BooleanField):
        value = True
    elif value in ("false", "False") and isinstance(field, dj_models.BooleanField):
        value = False
    elif isinstance(field, dj_models.DateField) and not isinstance(field, dj_models.DateTimeField):
        if isinstance(value, str) and "T" in value:
            value = value.split("T", 1)[0]

    return target_key, value


def _orm_fallback(method, endpoint, data=None, params=None):
    """
    Fallback to Django's direct ORM connection (TiDB / MySQL) when the external
    Node CRUD microservice is unreachable or returns a server/configuration error.
    """
    try:
        parts = [p for p in endpoint.strip("/").split("/") if p]
        if not parts:
            return None
        resource = parts[0]
        item_id = None
        if len(parts) > 1:
            try:
                item_id = int(parts[1])
            except ValueError:
                # Sub-action endpoint like incomes/summary/ -> not a plain CRUD row
                return None

        model = _get_model_map().get(resource)
        if model is None:
            return None

        if method == "GET":
            if item_id is not None:
                obj = model.objects.filter(pk=item_id).first()
                return _serialize_instance(obj) if obj else None

            filter_kwargs = {}
            for raw_key, raw_val in (params or {}).items():
                if "__" in raw_key:
                    base_field, op = raw_key.split("__", 1)
                else:
                    base_field, op = raw_key, None

                norm_field, norm_val = _normalize_orm_field_and_value(model, base_field, raw_val)
                if not norm_field:
                    continue

                if op == "in" and isinstance(norm_val, str):
                    norm_val = [v for v in norm_val.split(",") if v != ""]
                elif op == "isnull":
                    norm_val = str(raw_val).lower() == "true"

                lookup = f"{norm_field}__{op}" if op else norm_field
                filter_kwargs[lookup] = norm_val

            qs = model.objects.filter(**filter_kwargs)
            return [_serialize_instance(o) for o in qs]

        if method == "POST":
            create_kwargs = {}
            for raw_key, raw_val in (data or {}).items():
                norm_field, norm_val = _normalize_orm_field_and_value(model, raw_key, raw_val)
                if not norm_field:
                    continue
                field_obj = next((f for f in model._meta.concrete_fields if f.attname == norm_field or f.name == norm_field), None)
                if field_obj and (getattr(field_obj, "auto_now", False) or getattr(field_obj, "auto_now_add", False)):
                    continue
                create_kwargs[norm_field] = norm_val

            try:
                obj = model.objects.create(**create_kwargs)
            except Exception as create_err:
                if resource == "subscription-payments" and "1364" in str(create_err) and "'date'" in str(create_err):
                    from django.db import connection
                    with connection.cursor() as cursor:
                        cursor.execute("ALTER TABLE `djangoapp_subscriptionpayment` MODIFY COLUMN `date` date NULL")
                    obj = model.objects.create(**create_kwargs)
                else:
                    raise
            return _serialize_instance(obj)

        if method == "PATCH" and item_id is not None:
            obj = model.objects.filter(pk=item_id).first()
            if not obj:
                return None
            for raw_key, raw_val in (data or {}).items():
                norm_field, norm_val = _normalize_orm_field_and_value(model, raw_key, raw_val)
                if norm_field:
                    setattr(obj, norm_field, norm_val)
            obj.save()
            return _serialize_instance(obj)

        if method == "DELETE" and item_id is not None:
            deleted, _ = model.objects.filter(pk=item_id).delete()
            if not deleted:
                return None
            return {"message": f"{model.__name__} deleted", "deleted": deleted}

    except Exception as orm_err:
        print(f"ORM fallback error on {method} {endpoint}: {orm_err}")
    return None


def _should_use_orm_fallback(e):
    # Do not fall back during unit tests using TestResponse (which has no .content attribute)
    resp = getattr(e, "response", None)
    if resp is not None and not hasattr(resp, "content"):
        return False
    return True


def get_request(endpoint, **params):
    """GET <BACKEND_URL><endpoint>?<params>. Returns None on failure."""
    global _BACKEND_UNREACHABLE
    if not BACKEND_URL or _BACKEND_UNREACHABLE:
        return _orm_fallback("GET", endpoint, params=params)
    url = BACKEND_URL + endpoint
    try:
        response = requests.get(url, params=params, headers=_headers(), timeout=3)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        _log_request_error("GET", url, e)
        if _should_use_orm_fallback(e):
            _BACKEND_UNREACHABLE = True
            return _orm_fallback("GET", endpoint, params=params)
        return None


def post_request(endpoint, data=None, **params):
    """POST a JSON body to <BACKEND_URL><endpoint>. Returns None on failure."""
    global _BACKEND_UNREACHABLE
    if not BACKEND_URL or _BACKEND_UNREACHABLE:
        return _orm_fallback("POST", endpoint, data=data, params=params)
    url = BACKEND_URL + endpoint
    try:
        response = requests.post(url, json=data, params=params, headers=_headers(), timeout=3)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        _log_request_error("POST", url, e)
        if _should_use_orm_fallback(e):
            _BACKEND_UNREACHABLE = True
            return _orm_fallback("POST", endpoint, data=data, params=params)
        return None


def patch_request(endpoint, data=None, **params):
    """PATCH a JSON body to <BACKEND_URL><endpoint>. Return None on failure."""
    global _BACKEND_UNREACHABLE
    if not BACKEND_URL or _BACKEND_UNREACHABLE:
        return _orm_fallback("PATCH", endpoint, data=data, params=params)
    url = BACKEND_URL + endpoint
    try:
        response = requests.patch(url, json=data, params=params, headers=_headers(), timeout=3)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        _log_request_error("PATCH", url, e)
        if _should_use_orm_fallback(e):
            _BACKEND_UNREACHABLE = True
            return _orm_fallback("PATCH", endpoint, data=data, params=params)
        return None


def delete_request(endpoint, **params):
    """DELETE <BACKEND_URL><endpoint>. Return None on failure."""
    global _BACKEND_UNREACHABLE
    if not BACKEND_URL or _BACKEND_UNREACHABLE:
        return _orm_fallback("DELETE", endpoint, params=params)
    url = BACKEND_URL + endpoint
    try:
        response = requests.delete(url, params=params, headers=_headers(), timeout=3)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        _log_request_error("DELETE", url, e)
        if _should_use_orm_fallback(e):
            _BACKEND_UNREACHABLE = True
            return _orm_fallback("DELETE", endpoint, params=params)
        return None
