import socket

from requests import get

from sfkit.api import get_doc_ref_dict, update_firestore
from sfkit.api import get_user_email
from sfkit.protocol.utils.helper_functions import authenticate_user


def setup_networking(ports_str: str) -> None:
    authenticate_user()

    if ports_str:  # if ports are specified we're using website and internal ip_addresses
        ip_address: str = socket.gethostbyname(socket.gethostname())
        print("Using internal ip address:", ip_address)
    else:
        ip_address: str = get("https://api.ipify.org").content.decode("utf-8")
        print("Using external ip address:", ip_address)

    print("Processing...")
    update_firestore(f"update_firestore::IP_ADDRESS={ip_address}")

    doc_ref_dict: dict = get_doc_ref_dict()
    email: str = get_user_email()
    role: str = str(doc_ref_dict["participants"].index(email))
    if role == "0":
        if not ports_str:
            port1: str = validate_port(input("Enter port for Party 1: "))
            port2: str = validate_port(input("Enter port for Party 2: "))
            ports: list[str] = ["null", port1, port2]
            ports_str = ",".join(ports)
        update_firestore(f"update_firestore::PORTS={ports_str}")
    elif role == "1":
        if not ports_str:
            port = validate_port(input("Enter the port number you want to use to communicate with Party 2: "))
            ports: list[str] = ["null", "null", port]
            ports_str = ",".join(ports)
        update_firestore(f"update_firestore::PORTS={ports_str}")

    print("Successfully communicated networking information!")


def validate_port(port: str) -> str:
    if port.isdigit() and 1024 <= int(port) <= 65535:
        return port
    print("Invalid port number.  Please enter a number between 1024 and 65535.")
    exit(1)
