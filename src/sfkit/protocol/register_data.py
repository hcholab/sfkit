import os
import time

import checksumdir
from google.cloud import firestore
from sfkit.protocol.utils import constants
from sfkit.protocol.utils.google_cloud_pubsub import GoogleCloudPubsub
from sfkit.protocol.utils.helper_functions import confirm_authentication


def register_data() -> bool:
    email, study_title = confirm_authentication()
    doc_ref = firestore.Client().collection("studies").document(study_title.replace(" ", "").lower())
    doc_ref_dict = doc_ref.get().to_dict() or {}  # type: ignore
    role: str = str(doc_ref_dict["participants"].index(email))
    study_type: str = doc_ref_dict["type"]

    gcloudPubsub = GoogleCloudPubsub(constants.SERVER_GCP_PROJECT, role, study_title)

    data_path = input("Enter the (absolute) path to your data files: ")
    num_inds = validate_data(data_path, study_type, role=role)
    gcloudPubsub.publish(f"update_firestore::NUM_INDS={num_inds}::{study_title}::{email}")
    time.sleep(1)
    gcloudPubsub.publish(f"update_firestore::status=not ready::{study_title}::{email}")
    time.sleep(1)  # it seems to have trouble if I update both at the same time
    data_hash = checksumdir.dirhash(data_path, "md5")
    gcloudPubsub.publish(f"update_firestore::DATA_HASH={data_hash}::{study_title}::{email}")

    with open(os.path.join(constants.sfkit_DIR, "data_path.txt"), "w") as f:
        f.write(data_path + "\n")

    print("Successfully registered and validated data!")
    return True


def validate_data(data_path: str, study_type: str, role: str = "") -> int:
    print(f"Validating data for {study_type} study...")
    files_list = list(os.walk(data_path))  # consider using glob.glob
    # check that we have all the necessary files
    for needed_file in constants.NEEDED_INPUT_FILES[study_type]:
        if all(needed_file not in str(file) for file in files_list):
            print(f"You are missing the file {needed_file}.")
            exit(1)

    if study_type == "GWAS":
        rows = sum(1 for _ in open(os.path.join(data_path, "cov.txt")))
        assert rows == sum(1 for _ in open(os.path.join(data_path, "geno.txt")))
        assert rows == sum(1 for _ in open(os.path.join(data_path, "pheno.txt")))
        return rows
    elif study_type == "PCA":
        rows = sum(1 for _ in open(os.path.join(data_path, f"lung_split/pheno_party{role}.txt")))
        assert rows == sum(1 for _ in open(os.path.join(data_path, f"lung_split/cov_party{role}.txt")))
        return rows
    else:
        print("Unknown study type.")
        exit(1)
