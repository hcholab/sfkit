import requests

from sfkit.protocol.utils import constants


def website_get(request_type: str, params: dict) -> requests.Response:
    url = f"{constants.WEBSITE_URL}/{request_type}"
    headers = {
        "Authorization": f"Bearer {generate_jwt()}",
        "content-type": "application/json",
    }
    return requests.get(url, headers=headers, params=params)


def get_doc_ref_dict(study_title: str) -> dict:
    response = website_get("get_doc_ref_dict", {"study_title": study_title.replace(" ", "").lower()})
    return response.json()


def get_study_options() -> list:
    response = website_get("get_study_options", {})
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
