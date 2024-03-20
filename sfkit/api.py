from io import IOBase
from typing import Union

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
            # Note: NO content-type header set here
        }

    response = requests.post(url, files=files, headers=headers, params=params)

    return response.status_code == 200


def send_request(
    request_type: str, params: Union[dict, None] = None, data: Union[dict, None] = None, method: str = "GET"
) -> requests.Response:
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

    if method == "GET":
        return requests.get(url, headers=headers, params=params)
    elif method == "POST":
        return requests.post(url, headers=headers, json=data, params=params)
    else:
        raise ValueError(f"Invalid method: {method}")


def get_doc_ref_dict() -> dict:
    response = send_request("get_doc_ref_dict")
    return response.json()


def get_study_options() -> dict:
    response = requests.get(f"{constants.SFKIT_API_URL}/get_study_options", headers=get_service_account_headers())
    return response.json()


def get_username() -> str:
    response = send_request("get_username")
    return response.json().get("username", "")


def update_firestore(msg: str) -> bool:
    print(f"Updating firestore with msg: {msg}")
    response = send_request("update_firestore", params={"msg": msg})  # TODO: use POST once the API is updated
    return response.status_code == 200


def create_cp0() -> bool:
    response = send_request("create_cp0", method="POST")
    return response.status_code == 200


def get_service_account_headers():
    creds, _ = google.auth.default()
    creds = creds.with_scopes(["openid", "email", "profile"])  # type: ignore
    creds.refresh(GAuthRequest())
    if not creds.token:
        raise ValueError("No token found")
    return {
        AUTH_HEADER: BEARER_PREFIX + creds.token,
    }
