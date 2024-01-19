from io import IOBase

import google.auth
import requests
from google.auth.transport.requests import Request as GAuthRequest

from sfkit.utils import constants

AUTH_HEADER = "Authorization"
BEARER_PREFIX = "Bearer "

def website_send_file(file: IOBase, filename: str) -> bool:
    params = {}
    files = {"file": (filename, file)}
    url = f"{constants.SFKIT_API_URL}/upload_file"
    with open(constants.AUTH_KEY, "r") as f:
        auth_key = f.readline().rstrip()

    if auth_key.startswith("study_id:"):
        params["study_id"] = auth_key.split(":")[1]
        headers = get_service_account_headers()
    else:
        headers = {
            "Authorization": f"{auth_key}",
            "content-type": "application/json",
        }

    response = requests.post(url, files=files, headers=headers, params=params)

    return response.status_code == 200


def website_get(request_type: str, params: dict = None) -> requests.Response:
    if params is None:
        params = {}
    url = f"{constants.SFKIT_API_URL}/{request_type}"

    with open(constants.AUTH_KEY, "r") as f:
        auth_key = f.readline().rstrip()
    
    if auth_key.startswith("study_id:"):
        params["study_id"] = auth_key.split(":")[1]
        headers = get_service_account_headers()
    else:
        headers = {
            "Authorization": f"{auth_key}",
            "content-type": "application/json",
        }

    return requests.get(url, headers=headers, params=params)


def get_doc_ref_dict() -> dict:
    response = website_get("get_doc_ref_dict")
    return response.json()

def get_study_options() -> dict:
    response = requests.get(f"{constants.SFKIT_API_URL}/get_study_options", headers=get_service_account_headers())
    return response.json()

def get_username() -> str:
    response = website_get("get_username")
    return response.json().get("username", "")


def update_firestore(msg: str) -> bool:
    print(f"Updating firestore with msg: {msg}")
    response = website_get("update_firestore", params={"msg": msg})
    return response.status_code == 200


def create_cp0() -> bool:
    response = website_get("create_cp0")
    return response.status_code == 200


def get_service_account_headers():
    creds, _ = google.auth.default()
    creds = creds.with_scopes(["openid", "email", "profile"])
    creds.refresh(GAuthRequest())
    return {
        AUTH_HEADER: BEARER_PREFIX + creds.token,
    }