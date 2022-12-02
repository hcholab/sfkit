import time

from sfkit.api import get_doc_ref_dict, update_firestore
from sfkit.utils.gwas_protocol import run_gwas_protocol
from sfkit.utils.pca_protocol import run_pca_protocol
from sfkit.utils.sfgwas_protocol import run_sfgwas_protocol
from sfkit.api import create_cp0, get_user_email
from sfkit.utils.helper_functions import authenticate_user


def run_protocol(phase: str = "", demo: bool = False) -> None:
    authenticate_user()

    if phase and phase not in ["1", "2", "3"]:
        raise ValueError("phase must be 1, 2, or 3")

    doc_ref_dict: dict = get_doc_ref_dict()
    email = get_user_email()

    role: str = str(doc_ref_dict["participants"].index(email))
    study_type: str = doc_ref_dict["study_type"]
    statuses: dict = doc_ref_dict["status"]

    if (statuses[email] in ["validated data", "running1", "running2"]) or (
        role == "0" and statuses[email] == "ready to begin sfkit"
    ):
        statuses[email] = "ready to begin protocol"
        update_firestore("update_firestore::status=ready to begin protocol")
    if statuses[email] == "ready to begin protocol":
        while not demo and other_participant_not_ready(list(statuses.values())):
            print("Other participant(s) not yet ready.  Waiting... (press CTRL-C to cancel)")
            time.sleep(5)
            doc_ref_dict: dict = get_doc_ref_dict()
            statuses: dict = doc_ref_dict["status"]

        if role == "1":
            create_cp0()

        if phase:
            update_firestore(f"update_firestore::status=running phsae {phase} of {study_type} protocol")
        else:
            update_firestore(f"update_firestore::status=running {study_type} protocol")

        if study_type == "MPCGWAS":
            run_gwas_protocol(doc_ref_dict, role)
        elif study_type == "SFGWAS":
            run_sfgwas_protocol(role, phase, demo)
        elif study_type == "PCA":
            run_pca_protocol(role)
        else:
            raise ValueError(f"Unknown study type: {study_type}")
    else:
        print("Your status is not ready.  Exiting now.")
        return


def other_participant_not_ready(status_list: list) -> bool:
    return (
        "" in status_list
        or "FAILED" in str(status_list)
        or "ready to begin sfkit" in str(status_list)
        or "setting up your vm instance" in str(status_list)
    )
