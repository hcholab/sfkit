import os
import time

import checksumdir
from google.cloud import firestore
from sftools.protocol.utils import constants
from sftools.protocol.utils.google_cloud_pubsub import GoogleCloudPubsub


def validate_data(data_path: str, num_inds: int = 1000) -> None:
    # sourcery skip: for-index-underscore
    print("Validating data...")
    files_list = os.listdir(data_path)
    # check that we have all the necessary files
    for needed_file in constants.DATA_RAW_FILES:
        if all(needed_file not in file for file in files_list):
            print(f"You are missing the file {needed_file}.")
            exit(1)
    # check that all files in files_list have 1000 lines
    # for file in files_list:
    #     num_lines = sum(1 for line in open(os.path.join(data_path, file)))
    #     if num_lines != num_inds:
    #         print(f"The file {file} has {num_lines} lines instead of {num_inds}.")
    #         exit(1)
    print("Data is valid!")


def register_data() -> bool:
    with open(constants.AUTH_FILE, "r") as f:
        email = f.readline().rstrip()
        study_title = f.readline().rstrip()
    doc_ref = firestore.Client().collection("studies").document(study_title.replace(" ", "").lower())
    doc_ref_dict = doc_ref.get().to_dict() or {}  # type: ignore
    role: str = str(doc_ref_dict["participants"].index(email))

    data_path = input("Enter the (absolute) path to your data files: ")
    # TODO: update num_inds to be number of rows in geno.txt?
    validate_data(data_path, num_inds=int(doc_ref_dict["personal_parameters"][email]["NUM_INDS"]["value"]))

    data_hash = checksumdir.dirhash(data_path, "md5")

    gcloudPubsub = GoogleCloudPubsub(constants.SERVER_GCP_PROJECT, role, study_title)
    gcloudPubsub.publish(f"update_firestore::status=not ready::{study_title}::{email}")
    time.sleep(1)  # it seems to have trouble if I update both at the same time
    gcloudPubsub.publish(f"update_firestore::data_hash={data_hash}::{study_title}::{email}")

    with open(os.path.join(constants.SFTOOLS_DIR, "data_path.txt"), "w") as f:
        f.write(data_path + "\n")

    print("Successfully registered and validated data!")
    return True


def main():
    pass


if __name__ == "__main__":
    main()
