import os
import time

from google.cloud import firestore
from sftools.protocol.utils import constants
from sftools.protocol.utils.google_cloud_pubsub import GoogleCloudPubsub
from sftools.protocol.utils.gwas_protocol import run_gwas_protocol
from sftools.protocol.utils.sfgwas_protocol import run_sfgwas_protocol


def run_protocol() -> None:
    with open(constants.AUTH_FILE, "r") as f:
        email = f.readline().rstrip()
        study_title = f.readline().rstrip()
        sa_key_file = f.readline().rstrip()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = sa_key_file

    doc_ref = firestore.Client().collection("studies").document(study_title.replace(" ", "").lower())
    doc_ref_dict: dict = doc_ref.get().to_dict()  # type: ignore
    role: str = str(doc_ref_dict["participants"].index(email))
    study_type: str = doc_ref_dict["type"]
    statuses: dict = doc_ref_dict["status"]

    if statuses[email] in ["['']", "['validating']", "['invalid data']"]:
        print("You have not successfully validated your data.  Please do so before proceeding.")
        return

    gcloudPubsub = GoogleCloudPubsub(constants.SERVER_GCP_PROJECT, role, study_title)
    if statuses[email] == ["not ready"]:
        statuses[email] = ["ready"]
        gcloudPubsub.publish(f"update_firestore::status=ready::{study_title}::{email}")

    while any(s in str(statuses.values()) for s in ["['']", "['validating']", "['invalid data']", "['not ready']"]):
        print("The other participant is not yet ready.  Waiting... (press CTRL-C to cancel)")
        time.sleep(5)
        statuses = doc_ref.get().to_dict()["status"]  # type: ignore

    if statuses[email] == ["ready"]:
        gcloudPubsub.publish(f"update_firestore::status=running::{study_title}::{email}")

        if role == "1":
            print("Asking cp0 to set up their part as well...")
            time.sleep(1)
            gcloudPubsub.publish(f"run_protocol_for_cp0::{study_title}")

        if study_type == "GWAS":
            run_gwas_protocol(doc_ref_dict, role)
        elif study_type == "PCA":
            run_sfgwas_protocol(doc_ref_dict, role)
    else:
        print("You status is not ready.  Exiting now.")
        return


def main():
    pass


if __name__ == "__main__":
    main()
