import requests

from sfkit.protocol.utils import constants
from sfkit.protocol.utils.helper_functions import get_authentication


def website_get(request_type: str, params: dict, user_auth=True) -> requests.Response:
    if user_auth:
        user, study_title = get_authentication()
        params |= {"study_title": study_title.replace(" ", "").lower(), "user": user}

    url = f"{constants.WEBSITE_URL}/{request_type}"
    headers = {
        "Authorization": f"Bearer {generate_jwt()}",
        "content-type": "application/json",
    }
    return requests.get(url, headers=headers, params=params)


def get_doc_ref_dict() -> dict:
    response = website_get("get_doc_ref_dict", {})
    return response.json()


def get_study_options() -> list:
    response = website_get("get_study_options", {}, user_auth=False)
    return response.json().get("options")


def update_firestore(msg: str) -> bool:
    response = website_get("update_firestore", {"msg": msg})
    return response.status_code == 200


def get_github_token() -> dict:
    response = website_get("get_github_token", {})
    return response.json()


def generate_jwt() -> str:
    url: str = constants.METADATA_VM_IDENTITY_URL.format(constants.WEBSITE_URL, "full", "TRUE")
    response: requests.Response = requests.get(url, headers={"Metadata-Flavor": "Google"})
    response.raise_for_status()
    return response.text
