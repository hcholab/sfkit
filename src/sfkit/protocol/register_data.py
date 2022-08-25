import glob
import os

import checksumdir
from sfkit.protocol.utils import constants
from sfkit.protocol.utils.helper_functions import get_authentication
from sfkit.api import get_doc_ref_dict
from sfkit.api import update_firestore


def register_data(geno_binary_file_prefix: str, data_path: str) -> bool:

    email, study_title = get_authentication()
    doc_ref_dict: dict = get_doc_ref_dict()
    role: str = str(doc_ref_dict["participants"].index(email))
    study_type: str = doc_ref_dict["type"]

    if not geno_binary_file_prefix:
        geno_binary_file_prefix = input(
            f"Enter absolute path to geno binary file prefix (e.g. '/home/smendels/for_sfgwas/geno/lung_party1_chr%d'): "
        )  # sourcery skip: remove-redundant-fstring
    if not os.path.isabs(geno_binary_file_prefix):
        print("I need an ABSOLUTE path for the geno_binary_file_prefix.")
        exit(1)
    # if not os.path.exists(geno_binary_file_prefix):
    #     print("I need a valid path for the geno_binary_file_prefix.")
    #     exit(1)

    if not data_path:
        data_path = input("Enter the (absolute) path to your data files (e.g. /home/smendels/for_sfgwas): ")
    if not os.path.isabs(data_path):
        print("I need an ABSOLUTE path for the data_path.")
        exit(1)
    num_inds = validate_data(data_path, study_type, role=role)
    update_firestore(f"update_firestore::NUM_INDS={num_inds}::{study_title}::{email}")
    update_firestore(f"update_firestore::status=not ready::{study_title}::{email}")
    data_hash = checksumdir.dirhash(data_path, "md5")
    update_firestore(f"update_firestore::DATA_HASH={data_hash}::{study_title}::{email}")

    with open(os.path.join(constants.SFKIT_DIR, "data_path.txt"), "w") as f:
        f.write(geno_binary_file_prefix + "\n")
        f.write(data_path + "\n")

    print("Successfully registered and validated data!")
    return True


def validate_data(data_path: str, study_type: str, role: str = "") -> int:
    print(f"Validating data for {study_type} study...")
    files_list = glob.glob(f"{data_path}/**", recursive=True)
    pgen = True  # "pgen" if any(f.endswith(".pgen") for f in files_list) else ""
    # for needed_file in constants.NEEDED_INPUT_FILES[f"{study_type}_{pgen}"]:
    #     if all(needed_file not in str(file) for file in files_list):
    #         print(f"You are missing the file {needed_file}.")
    #         exit(1)
    if pgen:
        pheno_party_file = next(f for f in files_list if f.endswith("pheno.txt"))
        rows = num_rows(pheno_party_file)
        cov_party_file = next(f for f in files_list if f.endswith("cov.txt"))
        assert rows == num_rows(cov_party_file), "pheno and cov files have different number of lines"
        sample_keep_file = num_rows(next(f for f in files_list if f.endswith("sample_keep.txt")))
        assert rows == sample_keep_file, "sample_keep and pheno/cov files have different number of lines"
        print(f"The number of lines/rows is: {rows}")
        return rows
    elif study_type == "SFGWAS":
        rows = num_rows(os.path.join(data_path, f"lung_split/pheno_party{role}.txt"))
        assert rows == num_rows(os.path.join(data_path, f"lung_split/cov_party{role}.txt"))
        return rows
    elif study_type == "GWAS":
        rows = num_rows(os.path.join(data_path, "cov.txt"))
        assert rows == num_rows(os.path.join(data_path, "geno.txt"))
        assert rows == num_rows(os.path.join(data_path, "pheno.txt"))
        return rows
    else:
        print("Unknown study type.")
        exit(1)


def num_rows(file_path: str) -> int:
    return sum(1 for _ in open(file_path))
