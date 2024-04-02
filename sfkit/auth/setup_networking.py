import socket

from requests import get

from sfkit.api import get_doc_ref_dict, get_username, update_firestore
from sfkit.utils.helper_functions import authenticate_user

MAX_PARTICIPANTS = 10
MAX_THREADS = 100


def setup_networking(ports_str: str = "", ip_address: str = "") -> None:
    print("Setting up networking...")
    print(
        "NOTE: this step should be run after all participants have joined the study.  If you run this step before all participants have joined, you will need to re-run this step after all participants have joined."
    )

    authenticate_user()
    doc_ref_dict: dict = get_doc_ref_dict()
    role: int = doc_ref_dict["participants"].index(get_username())

    if not ip_address:
        if doc_ref_dict["setup_configuration"] == "website":
            ip_address = socket.gethostbyname(socket.gethostname())  # internal ip address
            print("Using internal ip address:", ip_address)
        else:
            ip_address = get("https://api.ipify.org").content.decode("utf-8")  # external ip address
            print("Using external ip address:", ip_address)

    print("Processing...")
    update_firestore(f"update_firestore::IP_ADDRESS={ip_address}")

    if ports_str:
        [validate_port(port) for port in ports_str.split(",")]
        # pad ports_str with nulls if necessary
        pad_length = len(doc_ref_dict["participants"]) - len(ports_str.split(","))
        if pad_length < 0:
            print(
                "WARNING: You have provided more ports than there are participants.  The extra ports will be ignored."
            )
            ports_str = ",".join(ports_str.split(",")[: len(doc_ref_dict["participants"])])
        ports_str = "null," * pad_length + ports_str
    elif doc_ref_dict["study_type"] == "SF-RELATE":
        default = ["null,3110,7320", "null,null,9210", "null,null,null"]
        ports_str = default[role]
    else:
        base = 8100 + MAX_PARTICIPANTS * MAX_THREADS * role
        ports = [base + MAX_THREADS * r for r in range(len(doc_ref_dict["participants"]))]
        ports_str = ",".join([str(p) for p in ports])

    update_firestore(f"update_firestore::PORTS={ports_str}")
    print("Successfully communicated networking information!")


def validate_port(port: str) -> str:
    if port.isdigit() and 1024 <= int(port) <= 65535:
        return port
    print(f"{port} is an invalid port number.  Please enter a number between 1024 and 65535.")
    exit(1)
