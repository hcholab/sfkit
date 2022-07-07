import socket

from google.cloud import firestore
from sftools.protocol.utils import constants
from sftools.protocol.utils.google_cloud_pubsub import GoogleCloudPubsub


def setup_networking():
    with open(constants.AUTH_FILE, "r") as f:
        email = f.readline().rstrip()
        study_title = f.readline().rstrip()

    # send pubsub to the website with my ip address and port
    ip_address = socket.gethostbyname(socket.gethostname())

    print("Processing...")

    collection = firestore.Client().collection("studies")
    doc_ref_dict = collection.document(study_title.replace(" ", "").lower()).get().to_dict() or {}  # type: ignore
    role: str = str(doc_ref_dict["participants"].index(email))
    gcloudPubsub = GoogleCloudPubsub(constants.SERVER_GCP_PROJECT, role, study_title)
    gcloudPubsub.publish(f"update_firestore::ip_address={ip_address}::{study_title}::{email}")

    # get port from user if role 1
    if role == "1":
        port = input("Enter the port number you want to use: ")  # used to communicate with P2
        ports = ["null", "null", port]
        gcloudPubsub.publish(f"update_firestore::ports={','.join(ports)}::{study_title}::{email}")

    print("Your networking options have been updated in the study parameters.")


def main():
    setup_networking()


if __name__ == "__main__":
    main()
