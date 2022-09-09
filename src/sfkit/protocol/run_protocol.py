import time

from sfkit.protocol.utils.gwas_protocol import run_gwas_protocol
from sfkit.protocol.utils.helper_functions import get_authentication
from sfkit.protocol.utils.sfgwas_protocol import run_sfgwas_protocol
from sfkit.api import get_doc_ref_dict
from sfkit.api import update_firestore


def run_protocol(phase: str = "") -> None:
    if phase and phase not in ["1", "2", "3"]:
        raise ValueError("phase must be 1, 2, or 3")

    email, study_title = get_authentication()

    doc_ref_dict: dict = get_doc_ref_dict()
    role: str = str(doc_ref_dict["participants"].index(email))
    study_type: str = doc_ref_dict["type"]
    statuses: dict = doc_ref_dict["status"]
    if statuses[email] in ["['']", "['validating']", "['invalid data']"]:
        print("You have not successfully validated your data.  Please do so before proceeding.")
        return

    if statuses[email] in [["not ready"], ["running1"], ["running2"]]:
        statuses[email] = ["ready"]
        update_firestore(f"update_firestore::status=ready::{study_title}::{email}")
    while any(s in str(statuses.values()) for s in ["['']", "['validating']", "['invalid data']", "['not ready']"]):
        print("The other participant is not yet ready.  Waiting... (press CTRL-C to cancel)")
        time.sleep(5)
        doc_ref_dict: dict = get_doc_ref_dict()
        statuses: dict = doc_ref_dict["status"]
    if statuses[email] == ["ready"]:
        update_firestore(f"update_firestore::status=running{phase}::{study_title}::{email}")
        if study_type in {"GWAS", "gwas"}:
            run_gwas_protocol(doc_ref_dict, role)
        elif study_type in {"SFGWAS", "sfgwas"}:
            run_sfgwas_protocol(study_title, role, phase)
    else:
        print("You status is not ready.  Exiting now.")
        return
