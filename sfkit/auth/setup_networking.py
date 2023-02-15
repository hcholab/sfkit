import socket
from time import sleep

from requests import get

from sfkit.api import get_doc_ref_dict, get_username, update_firestore
from sfkit.utils.helper_functions import authenticate_user


def setup_networking(ports_str: str) -> None:
    print("Setting up networking...")
    print(
        "NOTE: this step should be run after all participants have joined the study.  If you run this step before all participants have joined, you will need to re-run this step after all participants have joined."
    )

    authenticate_user()
    doc_ref_dict: dict = get_doc_ref_dict()

    if (
        doc_ref_dict["setup_configuration"] == "website"
    ):  # if ports are specified we're using auto-configuration and internal ip_addresses
        ip_address: str = socket.gethostbyname(socket.gethostname())
        print("Using internal ip address:", ip_address)
    else:
        ip_address: str = get("https://api.ipify.org").content.decode("utf-8")
        print("Using external ip address:", ip_address)

    print("Processing...")
    update_firestore(f"update_firestore::IP_ADDRESS={ip_address}")

    username: str = get_username()
    role: str = str(doc_ref_dict["participants"].index(username))

    if ports_str:
        [validate_port(port) for port in ports_str.split(",")]
    else:
        ports = ["null" for _ in range(len(doc_ref_dict["participants"]))]
        for r in range(int(role) + 1, len(doc_ref_dict["participants"])):  # for each other participant
            ports[r] = validate_port(input(f"Enter port you would like to use to conenct with participant #{r}: "))
        ports_str = ",".join(ports)

    update_firestore(f"update_firestore::PORTS={ports_str}")
    print("Successfully communicated networking information!")

    sleep(1)
    update_firestore("update_firestore::task=Configuring your VM instance completed")


def validate_port(port: str) -> str:
    if port.isdigit() and 1024 <= int(port) <= 65535:
        return port
    print("Invalid port number.  Please enter a number between 1024 and 65535.")
    exit(1)
