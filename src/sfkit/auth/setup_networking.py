from requests import get
from sfkit.protocol.utils.helper_functions import confirm_authentication
from sfkit.api import get_doc_ref_dict
from sfkit.api import update_firestore


def setup_networking():
    email, study_title = confirm_authentication()

    # internal_ip_address: str = socket.gethostbyname(socket.gethostname()) # this is internal ip_address
    external_ip_address: str = get("https://api.ipify.org").content.decode("utf-8")
    print("Using external ip address:", external_ip_address)

    print("Processing...")

    doc_ref_dict: dict = get_doc_ref_dict(study_title)
    role: str = str(doc_ref_dict["participants"].index(email))
    update_firestore(f"update_firestore::IP_ADDRESS={external_ip_address}::{study_title}::{email}")

    # get port from user if role 1
    if role == "1":
        port = input("Enter the port number you want to use (recommended is 8060): ")  # used to communicate with P2
        ports = ["null", "null", port]
        update_firestore(f"update_firestore::PORTS={','.join(ports)}::{study_title}::{email}")

    print("Your networking options have been updated in the study parameters.")
