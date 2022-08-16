from google.cloud import firestore
from requests import get
from sfkit.protocol.utils import constants
from sfkit.protocol.utils.google_cloud_pubsub import GoogleCloudPubsub
from sfkit.protocol.utils.helper_functions import confirm_authentication


def setup_networking():
    email, study_title = confirm_authentication()

    # send pubsub to the website with my ip address and port
    # internal_ip_address: str = socket.gethostbyname(socket.gethostname()) # this is internal ip_address
    external_ip_address: str = get("https://api.ipify.org").content.decode("utf-8")
    print("Using external ip address:", external_ip_address)

    print("Processing...")

    collection = firestore.Client().collection("studies")
    doc_ref_dict = collection.document(study_title.replace(" ", "").lower()).get().to_dict() or {}  # type: ignore
    role: str = str(doc_ref_dict["participants"].index(email))
    gcloudPubsub = GoogleCloudPubsub(constants.SERVER_GCP_PROJECT, role, study_title)
    gcloudPubsub.publish(f"update_firestore::IP_ADDRESS={external_ip_address}::{study_title}::{email}")

    # get port from user if role 1
    if role == "1":
        port = input("Enter the port number you want to use (recommended is 8060): ")  # used to communicate with P2
        ports = ["null", "null", port]
        gcloudPubsub.publish(f"update_firestore::PORTS={','.join(ports)}::{study_title}::{email}")

    print("Your networking options have been updated in the study parameters.")
