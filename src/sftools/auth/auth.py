import os

import pydata_google_auth
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sftools.protocol.utils import constants


def auth():
    """
    Logs in user with Google
    Gets study title
    """
    print("Logging in with Google...")
    credentials, _ = pydata_google_auth.default(scopes=["openid", "https://www.googleapis.com/auth/userinfo.email"])
    if "id_token" in credentials.__dict__.keys() or "_id_token" in credentials.__dict__.keys():
        email: str = id_token.verify_oauth2_token(credentials.id_token, google_requests.Request()).get("email")
    elif "_service_account_email" in credentials.__dict__.keys():
        email: str = credentials.service_account_email
    else:
        raise LookupError("Could not get email from credentials")
    print(f"Logged in as {email}")

    # save the email, study title to a file
    if not os.path.exists(constants.SFTOOLS_DIR):
        os.makedirs(constants.SFTOOLS_DIR)
    with open(constants.AUTH_FILE, "w") as f:
        f.write(f"{email}\n")

    print("You are now authenticated with the sftools CLI!")


def main():
    auth()


if __name__ == "__main__":
    main()
