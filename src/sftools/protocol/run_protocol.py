import os
import shutil
import subprocess

from google.cloud import firestore
from sftools.protocol.utils import constants
from sftools.protocol.utils.google_cloud_pubsub import GoogleCloudPubsub


def run_protocol() -> bool:
    with open(constants.AUTH_FILE, "r") as f:
        email = f.readline().rstrip()
        study_title = f.readline().rstrip()

    doc_ref = firestore.Client().collection("studies").document(study_title.replace(" ", "").lower())
    doc_ref_dict: dict = doc_ref.get().to_dict()  # type: ignore
    role: str = str(doc_ref_dict["participants"].index(email) + 1)
    data_path = "./encrypted_data"
    statuses: dict = doc_ref_dict["status"]

    if statuses[email] in ["['']", "['validating']", "['invalid data']"]:
        print("You have not successfully validated your data.  Please do so before proceeding.")
        return False

    gcloudPubsub = GoogleCloudPubsub(constants.SERVER_GCP_PROJECT, role, study_title)
    if statuses[email] == ["not ready"]:
        statuses[email] = ["ready"]
        gcloudPubsub.publish(f"update_firestore::status=ready::{study_title}::{email}")

    if any(s in str(statuses.values()) for s in ["['']", "['validating']", "['invalid data']", "['not ready']"]):
        print("The other participant is not yet ready.  Please try again once they are.")
        return False
    elif statuses[email] == ["ready"]:
        gcloudPubsub.publish(f"update_firestore::status=running::{study_title}::{email}")
        # subprocess.call([os.path.join(os.path.dirname(__file__), "utils/startup-script.sh"), data_path])
        # copy the startup script to current directory
        shutil.copyfile(os.path.join(os.path.dirname(__file__), "utils/startup-script.sh"), "startup-script.sh")
        # run the startup script
        hostname = f"{study_title.replace(' ', '').lower()}-{constants.INSTANCE_NAME_ROOT}{role}"
        subprocess.run(["sudo", "bash", "startup-script.sh", hostname, data_path])

        if role == "1":
            print("Asking cp0 to set up their part as well...")
            gcloudPubsub.publish(f"run_protocol_for_cp0::{study_title}::{email}")
    else:
        print("Something went wrong.  Please try again.")
        return False

    print("Set up is complete!  Your GWAS is now running.")
    return True


def main():
    pass


if __name__ == "__main__":
    main()
