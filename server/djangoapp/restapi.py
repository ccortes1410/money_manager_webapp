import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env.local', override=False)

# In docker-compose, "api" is the service name for the Node container, so
# it's resolvable by name on the shared Docker network -- no localhost/port
# juggling needed between containers.
_raw_backend_url = os.getenv('BACKEND_URL', default='http://api:3030/api/')
BACKEND_URL = _raw_backend_url if _raw_backend_url.endswith('/') else f"{_raw_backend_url}/"
INTERNAL_API_KEY = os.getenv('INTERNAL_API_KEY', default="")


def _headers():
    return {"x-internal-api-key": INTERNAL_API_KEY}


def _log_request_error(method, url, e):
    detail = ""
    if hasattr(e, "response") and e.response is not None and e.response.text:
        detail = f" - {e.response.text}"
    print(f"Error calling {method} {url}: {e}{detail}")


def get_request(endpoint, **params):
    """GET <BACKEND_URL><endpoint>?<params>. Returns None on failure."""
    url = BACKEND_URL + endpoint
    try:
        response = requests.get(url, params=params, headers=_headers(), timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        _log_request_error("GET", url, e)
        return None


def post_request(endpoint, data=None, **params):
    """POST a JSON body to <BACKEND_URL><endpoint>. Returns None on failure."""
    url = BACKEND_URL + endpoint
    try:
        response = requests.post(url, json=data, params=params, headers=_headers(), timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        _log_request_error("POST", url, e)
        return None


def patch_request(endpoint, data=None, **params):
    """PATCH a JSON body to <BACKEND_URL><endpoint>. Return None on failure."""
    url = BACKEND_URL + endpoint
    try:
        response = requests.patch(url, json=data, params=params, headers=_headers(), timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        _log_request_error("PATCH", url, e)
        return None


def delete_request(endpoint, **params):
    """DELETE <BACKEND_URL><endpoint>. Return None on failure."""
    url = BACKEND_URL + endpoint
    try:
        response = requests.delete(url, params=params, headers=_headers(), timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        _log_request_error("DELETE", url, e)
        return None
