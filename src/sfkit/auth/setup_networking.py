from requests import get
from sfkit.protocol.utils.helper_functions import get_authentication
from sfkit.api import get_doc_ref_dict
from sfkit.api import update_firestore


def setup_networking() -> None:
    (email, study_title) = get_authentication()

    # internal_ip_address: str = socket.gethostbyname(socket.gethostname())
    external_ip_address: str = get("https://api.ipify.org").content.decode("utf-8")
    print("Using external ip address:", external_ip_address)

    print("Processing...")
    update_firestore(f"update_firestore::IP_ADDRESS={external_ip_address}::{study_title}::{email}")

    doc_ref_dict: dict = get_doc_ref_dict()
    role: str = str(doc_ref_dict["participants"].index(email))
    if role == "0":
        port1: str = validate_port(input("Enter port for Party 1: "))
        port2: str = validate_port(input("Enter port for Party 2: "))
        ports: list[str] = ["null", port1, port2]
        update_firestore(f"update_firestore::PORTS={','.join(ports)}::{study_title}::{email}")
    elif role == "1":
        port = validate_port(input("Enter the port number you want to use to communicate with Party 2: "))
        ports: list[str] = ["null", "null", port]
        update_firestore(f"update_firestore::PORTS={','.join(ports)}::{study_title}::{email}")

    print("Successfully communicated networking information!")


def validate_port(port: str) -> str:
    if port.isdigit() and 1024 <= int(port) <= 65535:
        return port
    print("Invalid port number.  Please enter a number between 1024 and 65535.")
    exit(1)
