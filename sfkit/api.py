from io import IOBase

import requests

from sfkit.utils import constants


def website_send_file(file: IOBase, filename: str) -> bool:
    files = {"file": (filename, file)}
    url = f"{constants.SFKIT_API_URL}/upload_file"
    with open(constants.AUTH_KEY, "r") as f:
        auth_key = f.readline().rstrip()

    headers = {
        "Authorization": f"{auth_key}",
        # "content-type": "application/json",
    }
    response = requests.post(url, files=files, headers=headers)

    return response.status_code == 200


def website_get(request_type: str, params: dict = None) -> requests.Response:
    if params is None:
        params = {}
    url = f"{constants.SFKIT_API_URL}/{request_type}"

    with open(constants.AUTH_KEY, "r") as f:
        auth_key = f.readline().rstrip()

    headers = {
        "Authorization": f"{auth_key}",
        "content-type": "application/json",
    }
    return requests.get(url, headers=headers, params=params)


def get_doc_ref_dict() -> dict:
    response = website_get("get_doc_ref_dict")
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
