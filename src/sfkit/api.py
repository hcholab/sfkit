import requests

from sfkit.utils import constants


def website_get(request_type: str, params: dict = dict()) -> requests.Response:
    url = f"{constants.WEBSITE_URL}/{request_type}"

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


def get_user_email() -> str:
    response = website_get("get_user_email")
    return response.json().get("user_email", "")


def update_firestore(msg: str) -> bool:
    response = website_get("update_firestore", params={"msg": msg})
    return response.status_code == 200


def create_cp0() -> bool:
    response = website_get("create_cp0")
    return response.status_code == 200
