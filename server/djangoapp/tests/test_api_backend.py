"""
A minimal in-memory fake of the Node database API's generic CRUD router
(server/database/routes/crud.js), for testing Django views/services that
now talk to it over HTTP via djangoapp/restapi.py.

Usage in a test's setUp():
    
    from .test_api_backend import TestApiBackend
    from unittest.mock import patch
    
    self.test_api = TestApiBackend()
    for verb in ("ger", "post", "patch", "delete"):
        patcher = patch(f"djangoapp.restapi.requests.{verb}",
                        side_effect=getattr(self.test_api, verb))
        patcher.start()
        self.addCleanup(patcher.stop)

Then seed rows directly:

    self.test_api.seed("budgets", {"user_id": 1, "category": "Food", ...})
    
Rows should use the same shapes the real API returns -- date fields as
ISO strings, decimal fields as strings or numbers -- sine that's what the
adapters in djangoapp/services/api_adapters.py expect to parse.
"""
from collections import defaultdict

import requests


class TestResponse:
    """Mimics just enough of requests.Response for restapi.py's usage."""

    def __init__(self, data, status_code):
        self._data = data
        self.status_code = status_code

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error", response=self)


class TestApiBackend:
    def __init__(self):
        self.resources = defaultdict(list)
        self._next_id = defaultdict(lambda: 1)

    # ---- test setup helpers ----
    def seed(self, resource, row):
        row = dict(row)
        if row.get("id") is None:
            row["id"] = self._next_id[resource]
        self._next_id[resource] = max(self._next_id[resource], row["id"] + 1)
        self.resources[resource].append(row)
        return row

    # ---- internal helpers ----

    def _parse_path(self, url):
        # Everything after "/api/" is "<resource>" or "<resource>/<id>",
        # matching how restapi.BACKEND_URL + endpoint is built.
        path = url.split("/api/", 1)[1] if "/api/" in url else url
        parts = path.strip("/").split("/")
        resource = parts[0]
        item_id = None
        if len(parts) > 1 and parts[1]:
            # Only treat as ID if it's a number
            try:
                item_id = int(parts[1])
            except ValueError:
                # Not a number, treat as part of resource path (e.g., /incomes/summary/)
                item_id = None
        return resource, item_id

    def _compare(self, row_value, op, value):
        if op == "in":
            return str(row_value) in value.split(",")
        if op == "icontains":
            return str(value).lower() in str(row_value).lower()
        if op == "ne":
            return str(row_value) != str(value)
        if op in ("gte", "lte", "gt", "lt"):
            try:
                a, b = float(row_value), float(value)
            except (TypeError, ValueError):
                a, b = str(row_value), str(value) # works for ISO date strings
            return {"gte": a >= b, "lte": a <= b, "gt": a > b, "lt": a < b}[op]
        return str(row_value) == str(value) # exact match, no operator

    def _matches(self, row, filters):
        for key, value in filters.items():
            field, _, op = key.partition("__")
            if not self._compare(row.get(field), op or None, value):
                return False
        return True

    # ---- verbs, matching requests.get/post/patch/delete signatures ----

    def get(self, url, params=None, headers=None, timeout=None, **kwargs):
        resource, item_id = self._parse_path(url)
        if item_id is not None:
            row = next((r for r in self.resources[resource] if r["id"] == item_id), None)
            return TestResponse(row, 200 if row else 404)
        rows = [r for r in self.resources[resource] if self._matches(r, params or {})]
        return TestResponse(rows, 200)

    def post(self, url, json=None, headers=None, timeout=None, **kwargs):
        resource, item_id = self._parse_path(url)
        row = self.seed(resource, json or {})
        return TestResponse(row, 201)

    def patch(self, url, json=None, headers=None, timeout=None, **kwargs):
        resource, item_id = self._parse_path(url)
        row = next((r for r in self.resources[resource] if r["id"] == item_id), None)
        if not row:
            return TestResponse({"error": "not found"}, 404)
        row.update(json or {})
        return TestResponse(row, 200)

    def delete(self, url, headers=None, timeout=None, **kwargs):
        resource, item_id = self._parse_path(url)
        before = len(self.resources[resource])
        self.resources[resource] = [r for r in self.resources[resource] if r["id"] != item_id]
        if len(self.resources[resource]) == before:
            return TestResponse({"error": "not found"}, 404)
        return TestResponse({"message": "deleted"}, 200)
        