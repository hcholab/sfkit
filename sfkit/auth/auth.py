import os

from sfkit.api import get_doc_ref_dict
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
        print("auth_key.txt not found.")
        auth_key_path = input("Enter the path to your auth_key.txt file: ")
        try:
            with open(auth_key_path, "r") as f:
                auth_key = f.readline().rstrip()
        except FileNotFoundError:
            print("auth_key.txt not found.  Please download the auth_key.txt file from the sfkit website.")
            exit(1)

    os.makedirs(constants.SFKIT_DIR, exist_ok=True)
    with open(constants.AUTH_KEY, "w") as f:
        f.write(auth_key)

    try:
        assert get_doc_ref_dict() is not None
    except Exception as e:
        os.remove(constants.AUTH_KEY)
        print("Invalid auth_key.txt file.")
        print(e)
        condition_or_fail(False)
        exit(1)

    print("Successfully authenticated!")
