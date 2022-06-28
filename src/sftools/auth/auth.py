import os

import pydata_google_auth
from google.auth.transport import requests as google_requests
from google.cloud import firestore
from google.oauth2 import id_token


def auth():
    """
    Logs in user with Google
    Gets study title
    """
    print("Logging in with Google...")
    credentials, _ = pydata_google_auth.default(scopes=["openid", "https://www.googleapis.com/auth/userinfo.email"])
    email: str = id_token.verify_oauth2_token(credentials.id_token, google_requests.Request()).get("email")
    print(f"Logged in as {email}")

    study_title: str = input("Enter study title (same study title as on the website): ")
    doc_ref = firestore.Client().collection("studies").document(study_title.replace(" ", "").lower())
    doc_ref_dict = doc_ref.get().to_dict() or {}  # type: ignore
    if not doc_ref_dict:  # validate study title
        print("The study you entered was not found.")
        exit(1)

    if email not in doc_ref_dict["participants"]:  # validate email
        print("The email you entered was not found in the study.")
        exit(1)

    # save the email, study title to a file
    if not os.path.exists(os.path.expanduser("~/.config/sftools")):
        os.makedirs(os.path.expanduser("~/.config/sftools"))
    with open(os.path.expanduser("~/.config/sftools/auth.txt"), "w") as f:
        f.write(f"{study_title}\n{email}\n")

    print("You are now authenticated with the sftools CLI!")


def main():
    auth()


if __name__ == "__main__":
    main()
