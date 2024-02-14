import os

from sfkit.api import get_doc_ref_dict, get_service_account_headers, get_study_options
from sfkit.utils import constants
from sfkit.utils.helper_functions import condition_or_fail


def read_auth_key(file_path):
    try:
        with open(file_path, "r") as file:
            return file.readline().rstrip()
    except FileNotFoundError:
        return None


def get_study_index(study_options, study_id):
    if study_id:
        for i, study in enumerate(study_options):
            if study["study_id"] == study_id:
                return i
        print(f"Cannot find study with id {study_id}.")
        exit(1)
    elif len(study_options) == 1:
        return 0
    else:
        for i, study in enumerate(study_options):
            print(f"{i}: {study.get('title')}")
        while True:
            study_index = input("Enter the number of the study you want to use: ")
            if study_index.isdigit() and int(study_index) < len(study_options):
                return int(study_index)
            print("That input was invalid. Please try again.")


def auth(study_id: str) -> None:
    """
    Authenticate a GCP service account from the study with the sfkit CLI.
    """

    auth_key = read_auth_key("auth_key.txt")
    if auth_key is None:
        try:
            get_service_account_headers()
        except Exception as error:
            print("auth_key.txt not found.")
            auth_key_path = input("Enter the path to your auth_key.txt file: ")
            auth_key = read_auth_key(auth_key_path)
            if auth_key is None:
                print("auth_key.txt not found.  Please download the auth_key.txt file from the sfkit website.")
                exit(1)
        else:
            study_options = get_study_options().get("options")
            if not study_options:
                print(
                    "Cannot find study. Please join a user-configured study or download an auth_key.txt from an existing study."
                )
                exit(1)
            study_index = get_study_index(study_options, study_id)
            auth_key = "study_id:" + study_options[study_index]["study_id"]

    os.makedirs(constants.SFKIT_DIR, exist_ok=True)
    with open(constants.AUTH_KEY, "w") as file:
        file.write(auth_key)

    try:
        doc_ref_dict = get_doc_ref_dict()
        assert doc_ref_dict is not None and "title" in doc_ref_dict
    except Exception as error:
        os.remove(constants.AUTH_KEY)
        print("Invalid auth_key.txt file.")
        print(error)
        condition_or_fail(False, "sfkit auth failed.")
    else:
        print(f"Successfully authenticated with study {doc_ref_dict['title']}!")
