import json
import os

from google.cloud import firestore
from google.auth.transport import requests as google_requests
from sfkit.protocol.utils import constants


def auth():
    # get path to service account private key file
    sa_key_file = input("Enter absolute path to service account private key file: ")
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = sa_key_file

    with open(sa_key_file, "r") as f:
        data = json.load(f)
        sa_email = data["client_email"]

    # confirm that the service account private key file is valid
    try:
        google_requests.Request()  # basic check to make sure the key is valid
    except Exception as e:
        print(f"Error: {e}")
        print("Please make sure the service account private key file is valid.")
        exit(1)

    # get email and study title for this service account from the database
    study_title, user_email = "", ""
    collection = firestore.Client().collection("studies")
    for doc_ref in collection.stream():  # type: ignore
        doc_ref_dict = doc_ref.to_dict() or {}
        for user in doc_ref_dict["participants"]:
            if doc_ref_dict["personal_parameters"][user]["SA_EMAIL"]["value"] == sa_email:
                study_title = doc_ref.id
                user_email = user
                break
        if user_email:
            break
    if not user_email:
        print("Error finding your study.  Please make sure you service account key corresponds to a valid study.")
        exit(1)

    # if path to constants.AUTH_FILE does not exist, create it
    os.makedirs(constants.sfkit_DIR, exist_ok=True)
    with open(constants.AUTH_FILE, "w") as f:
        f.write(user_email + "\n")
        f.write(study_title + "\n")
        f.write(f"{sa_key_file}\n")

    print("Successfully authenticated!")
