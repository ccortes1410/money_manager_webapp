import requests
import os
from dotenv import load_dotenv

load_dotenv()

backend_url = os.getenv('backend_url', default="http://localhost:3030/")

def get_request(endpoint, **kwargs):
    if (kwargs):
        params = "&".join([f"{key}={value}" for key, value in kwargs.items()])
    request_url = backend_url + endpoint

    print("GET from {}".format(request_url))
    try:
        response = requests.get(request_url)
    except Exception as e:
        print("Error occurred: {}".format(e))
    return response.json()

# def get_budget(endpoint, budget_id):
#     if budget_id:
#         request_url = backend_url + endpoint
#     try:
#         response = requests.get(request_url)
#     except Exception as e:
#         print("Error occurred: {}".format(e))
#     return response.json()
