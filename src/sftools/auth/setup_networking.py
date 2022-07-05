import socket
import time

from google.cloud import firestore
from sftools.protocol.utils import constants
from sftools.protocol.utils.google_cloud_pubsub import GoogleCloudPubsub


def setup_networking():
    with open(constants.AUTH_FILE, "r") as f:
        email = f.readline().rstrip()
        study_title = f.readline().rstrip()

    # send pubsub to the website with my ip address and port
    ip_address = socket.gethostbyname(socket.gethostname())

    # get 2 ports from user
    ports = input("Please enter the ports you want to use (separated by a comma): ").split(",")
    if len(ports) != 2:
        print("Invalid number of ports.")
        return
    print("Processing...")

    collection = firestore.Client().collection("studies")
    doc_ref_dict = collection.document(study_title.replace(" ", "").lower()).get().to_dict() or {}  # type: ignore
    role: str = str(doc_ref_dict["participants"].index(email) + 1)
    gcloudPubsub = GoogleCloudPubsub(constants.SERVER_GCP_PROJECT, role, study_title)
    gcloudPubsub.publish(f"update_firestore::ip_address={ip_address}::{study_title}::{email}")
    time.sleep(1)
    gcloudPubsub.publish(f"update_firestore::ports={','.join(ports)}::{study_title}::{email}")
    print("Your networking options (ip address and port) have been updated in the study parameters.")


def main():
    setup_networking()


if __name__ == "__main__":
    main()
