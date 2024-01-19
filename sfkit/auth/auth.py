import os

from sfkit.api import get_doc_ref_dict, get_service_account_headers, get_study_options
from sfkit.utils import constants
from sfkit.utils.helper_functions import condition_or_fail

def auth() -> None:
    """
    Authenticate a GCP service account from the study with the sfkit CLI.
    """

    try:
        with open("auth_key.txt", "r") as f:
            auth_key = f.readline().rstrip()
    except FileNotFoundError:
        try:
            get_service_account_headers()
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
            study_options: list = get_study_options()["options"]
            if not study_options:
                print("Cannot find study. Please join a user-configured study or download an auth_key.txt from an existing study.")
                exit(1)
            if len(study_options) == 1:
                study_index = 0
            else:
                for i, study in enumerate(study_options):
                    print(f"{i}: {study.get('title')}")
                study_index = input("Enter the number of the study you want to use: ")
                while not study_index.isdigit() or int(study_index) >= len(study_options):
                    study_index = input("That input was invalid. Please enter the number of the study you want to use: ")
            auth_key = "study_id:" + study_options[int(study_index)]["study_id"]

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