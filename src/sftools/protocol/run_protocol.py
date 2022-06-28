import os
import shutil
import socket
import subprocess
import sys

from google.cloud import firestore
from sftools.protocol.utils import constants
from sftools.protocol.utils.google_cloud_compute import GoogleCloudCompute
from sftools.protocol.utils.google_cloud_pubsub import GoogleCloudPubsub
from sftools.protocol.utils.utils import create_instance_name


def run_protocol() -> bool:
    with open("auth.txt", "r") as f:
        study_title = f.readline().rstrip()
        email = f.readline().rstrip()

    doc_ref = firestore.Client().collection("studies").document(study_title.replace(" ", "").lower())
    doc_ref_dict: dict = doc_ref.get().to_dict()  # type: ignore
    role: str = str(doc_ref_dict["participants"].index(email) + 1)
    data_path = doc_ref_dict["personal_parameters"][email]["DATA_PATH"]["value"]
    statuses: dict = doc_ref_dict["status"]

    if statuses[email] in ["['']", "['validating']", "['invalid data']"]:
        print("You have not successfully validated your data.  Please do so before proceeding.")
        return False

    if statuses[email] == ["not ready"]:
        statuses[email] = ["ready"]  # TODO: update firestore that I'm ready

    if any(s in str(statuses.values()) for s in ["['']", "['validating']", "['invalid data']", "['not ready']"]):
        print("The other participant is not yet ready.  Please try again once they are.")
        return False
    elif statuses[email] == ["ready"]:
        gcloudPubsub = GoogleCloudPubsub(constants.SERVER_GCP_PROJECT, role, study_title)
        gcloudPubsub.publish(f"update_firestore::status=running::{study_title}::{email}")
        # subprocess.call([os.path.join(os.path.dirname(__file__), "utils/startup-script.sh"), data_path])
        # copy the startup script to current directory
        shutil.copyfile(os.path.join(os.path.dirname(__file__), "utils/startup-script.sh"), "startup-script.sh")
        # run the startup script
        subprocess.call(["bash", "startup-script.sh", data_path])

        if role == "1":
            print("Asking cp0 to set up their part as well...")
            gcp_project = doc_ref_dict["personal_parameters"][email]["GCP_PROJECT"]["value"]
            gcloudCompute = GoogleCloudCompute(gcp_project)
            member: str = f"serviceAccount:{gcloudCompute.get_service_account_for_vm(constants.SERVER_ZONE, socket.gethostname())}"
            # TODO: prob better way than needing member to get storage permissions...
            gcloudPubsub.publish(f"run_protocol_for_cp0::{study_title}::{member}::{email}")

    print("Set up is complete!  Your GWAS is now running.")
    return True


def main():
    pass


if __name__ == "__main__":
    main()
