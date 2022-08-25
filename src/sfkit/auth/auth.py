import os

from sfkit.protocol.utils import constants
from sfkit.api import get_study_options


def auth(study_title: str) -> None:
    """
    Authenticate a GCP service account from the study with the sfkit CLI.
    """

    if study_title:
        user_email = "Broad"
    else:
        study_title, user_email = "", ""

        options = get_study_options()
        if not options:
            print(
                "Error finding your study.  Please make sure you are part of a study and have uploaded your service account email to the website."
            )
            exit(1)
        if len(options) == 1:
            study_title, user_email = options[0]
        else:
            print("Please select your study:")
            for i, option in enumerate(options):
                print(f"{i}: {option[0]}")
            study_title, user_email = options[int(input("Enter your selection: "))]

    # if path to constants.AUTH_FILE does not exist, create it
    os.makedirs(constants.SFKIT_DIR, exist_ok=True)
    with open(constants.AUTH_FILE, "w") as f:
        f.write(user_email + "\n")
        f.write(study_title + "\n")

    print("Successfully authenticated!")
