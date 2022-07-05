import os
import time

import checksumdir
from google.cloud import firestore
from sftools.protocol.utils import constants
from sftools.protocol.utils.google_cloud_pubsub import GoogleCloudPubsub


def register_data() -> bool:
    with open(constants.AUTH_FILE, "r") as f:
        email = f.readline().rstrip()
        study_title = f.readline().rstrip()
    doc_ref = firestore.Client().collection("studies").document(study_title.replace(" ", "").lower())
    doc_ref_dict = doc_ref.get().to_dict() or {}  # type: ignore
    role: str = str(doc_ref_dict["participants"].index(email) + 1)

    data_path = input("Enter the (absolute) path to your data files: ")
    files_list = os.listdir(data_path)
    for needed_file in constants.DATA_RAW_FILES:
        if all(needed_file not in file for file in files_list):
            print(f"You are missing the file {needed_file}.")
            return False
    data_hash = checksumdir.dirhash(data_path, "md5")
    gcloudPubsub = GoogleCloudPubsub(constants.SERVER_GCP_PROJECT, role, study_title)
    gcloudPubsub.publish(f"update_firestore::status=not ready::{study_title}::{email}")
    time.sleep(1)
    gcloudPubsub.publish(f"update_firestore::data_hash={data_hash}::{study_title}::{email}")

    data_path_path = os.path.join(constants.SFTOOLS_DIR, "data_path.txt")
    with open(data_path_path, "w") as f:
        f.write(data_path + "\n")

    print("Successfully validated data!")
    return True


def main():
    pass


if __name__ == "__main__":
    main()
