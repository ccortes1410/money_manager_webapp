import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env.local')

# In docker-compose, "api" is the service name for the Node container, so
# it's resolvable by name on the shared Docker network -- no localhost/port
# juggling needed between containers.
BACKEND_URL = os.getenv('BACKEND_URL', default='http://api:3030/api/')
INTERNAL_API_KEY = os.getenv('INTERNAL_API_KEY', default="")


def _headers():
    return {"x-internal-api-key": INTERNAL_API_KEY}


def get_request(endpoint, **params):
    """GET <BACKEND_URL><endpoint>?<params>. Returns None on failure."""
    url = BACKEND_URL + endpoint
    try:
        response = requests.get(url, params=params, headers=_headers(), timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error calling GET {url}: {e}")
        return None


def post_request(endpoint, data=None, **params):
    """POST a JSON body to <BACKEND_URL><endpoint>. Returns None on failure."""
    url = BACKEND_URL + endpoint
    try:
        response = requests.post(url, json=data, params=params, headers=_headers(), timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error calling POST {url}: {e}")
        # Try to get error response details if available
        if hasattr(e, 'response') and e.response is not None:
            try:
                return e.response.json()  # Return the error details from backend
            except:
                pass  # If we can't parse JSON, fall through to return None
        return None


def patch_request(endpoint, data=None, **params):
    """PATCH a JSON body to <BACKEND_URL><endpoint>. Return None on failure."""
    url = BACKEND_URL + endpoint
    try:
        response = requests.patch(url, json=data, params=params, headers=_headers(), timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error calling PATCH {url}: {e}")
        return None


def delete_request(endpoint, **params):
    """DELETE <BACKEND_URL><endpoint>. Return None on failure."""
    url = BACKEND_URL + endpoint
    try:
        response = requests.delete(url, params=params, headers=_headers(), timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error calling DELETE {url}: {e}")
        return None
