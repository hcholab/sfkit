import os

import google.auth
from google.auth.transport.requests import Request as GAuthRequest

from sfkit.api import get_doc_ref_dict, get_study_options
from sfkit.utils import constants
from sfkit.utils.helper_functions import condition_or_fail

AUTH_HEADER = "Authorization"
BEARER_PREFIX = "Bearer "

def auth() -> None:
    """
    Authenticate a GCP service account from the study with the sfkit CLI.
    """

    try:
        with open("auth_key.txt", "r") as f:
            auth_key = f.readline().rstrip()
    except FileNotFoundError:
        try:
            headers = get_service_account_headers()
        except Exception as e:
            print("auth_key.txt not found.")
            auth_key_path = input("Enter the path to your auth_key.txt file: ")
            try:
                with open(auth_key_path, "r") as f:
                    auth_key = f.readline().rstrip()
            except FileNotFoundError:
                print("auth_key.txt not found.  Please download the auth_key.txt file from the sfkit website.")
                exit(1)
        else:
            study_options = get_study_options(headers)
            if study_options is None:
                print("Cannot find study. Please join a user-configured study or download an auth_key.txt from an existing study.")
                exit(1)
            for i, study in enumerate(study_options):
                print(f"{i}: {study.get('title')}")
            study_index = input("Enter the number of the study you want to use: ")
            while not study_index.isdigit() or int(study_index) >= len(study_options):
                study_index = input("That input was invalid. Please enter the number of the study you want to use: ")
            auth_key = study_options[int(study_index)]["auth_key"]

    os.makedirs(constants.SFKIT_DIR, exist_ok=True)
    with open(constants.AUTH_KEY, "w") as f:
        f.write(auth_key)

    try:
        doc_ref_dict = get_doc_ref_dict()
        assert doc_ref_dict is not None and "title" in doc_ref_dict
    except Exception as e:
        os.remove(constants.AUTH_KEY)
        print("Invalid auth_key.txt file.")
        print(e)
        condition_or_fail(False, "sfkit auth failed.")
    else:
        print(f"Successfully authenticated with study {doc_ref_dict['title']}!")


def get_service_account_headers():
    print("Trying to authenticate with Google Cloud Platform...")
    creds, _ = google.auth.default()
    creds = creds.with_scopes(["openid", "email", "profile"])
    creds.refresh(GAuthRequest())
    return {
        AUTH_HEADER: BEARER_PREFIX + creds.token,
    }