import os
import time

import checksumdir
from google.cloud import firestore
from sftools.protocol.utils import constants
from sftools.protocol.utils.google_cloud_pubsub import GoogleCloudPubsub


def validate_data(data_path: str, study_type: str, role: str = "") -> int:
    print(f"Validating data for {study_type} study...")
    files_list = os.walk(data_path)  # consider using glob.glob
    # check that we have all the necessary files
    for needed_file in constants.NEEDED_INPUT_FILES[study_type]:
        if all(needed_file not in file for file in files_list):
            print(f"You are missing the file {needed_file}.")
            exit(1)

    if study_type == "GWAS":
        rows = sum(1 for _ in open(os.path.join(data_path, "cov.txt")))
        assert rows == sum(1 for _ in open(os.path.join(data_path, "geno.txt"))), "rows in cov.txt and geno.txt differ"
        assert rows == sum(
            1 for _ in open(os.path.join(data_path, "pheno.txt"))
        ), "rows in cov.txt and pheno.txt differ"
        return rows
    elif study_type == "PCA":
        rows = sum(1 for _ in open(os.path.join(data_path, f"lung_split/pheno_party{role}.txt")))
        assert rows == sum(
            1 for _ in open(os.path.join(data_path, f"lung_split/cov_party{role}.txt"))
        ), f"rows in pheno_party{role}.txt and cov_party{role}.txt differ"
        return rows
    else:
        print("Unknown study type.")
        exit(1)


def register_data() -> bool:
    with open(constants.AUTH_FILE, "r") as f:
        email = f.readline().rstrip()
        study_title = f.readline().rstrip()
        sa_key_file = f.readline().rstrip()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = sa_key_file

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

    with open(os.path.join(constants.SFTOOLS_DIR, "data_path.txt"), "w") as f:
        f.write(data_path + "\n")

    print("Successfully registered and validated data!")
    return True


def main():
    pass


if __name__ == "__main__":
    main()
