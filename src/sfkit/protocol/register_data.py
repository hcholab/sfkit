import os

import checksumdir
from sfkit.protocol.utils import constants
from sfkit.protocol.utils.helper_functions import get_authentication
from sfkit.api import get_doc_ref_dict
from sfkit.api import update_firestore


def register_data(geno_binary_file_prefix: str, data_path: str) -> bool:
    """
    Register data with the server and validate that the data formatting looks correct.
    """

    email, study_title = get_authentication()
    doc_ref_dict: dict = get_doc_ref_dict()
    study_type = doc_ref_dict["study_type"]
    num_inds: int

    if study_type == "SFGWAS":
        geno_binary_file_prefix = validate_geno_binary_file_prefix(geno_binary_file_prefix)
        data_path = validate_data_path(data_path)

        if data_path == "demo":
            return using_demo(study_title, email)

        num_inds = validate_sfgwas_data(geno_binary_file_prefix, data_path)
        num_snps = num_rows(os.path.join(data_path, "snp_ids.txt"))
        update_firestore(f"update_firestore::NUM_INDS={num_inds}::{study_title}::{email}")
        update_firestore(f"update_firestore::NUM_SNPS={num_snps}::{study_title}::{email}")
        print(f"Your data has {num_inds} individuals and {num_snps} SNPs.")
    elif study_type == "MPCGWAS":
        data_path = validate_data_path(data_path)

        if data_path == "demo":
            return using_demo(study_title, email)

        num_inds = validate_mpcgwas_data(data_path)
        update_firestore(f"update_firestore::NUM_INDS={num_inds}::{study_title}::{email}")
        print(f"Your data has {num_inds} individuals.")
    elif study_type == "PCA":
        data_path = validate_data_path(data_path)

        if data_path == "demo":
            return using_demo(study_title, email)

        number_of_rows = num_rows(os.path.join(data_path, "data.txt"))
        number_of_cols = num_cols(os.path.join(data_path, "data.txt"))
        update_firestore(f"update_firestore::NUM_INDS={number_of_rows}::{study_title}::{email}")
        update_firestore(f"update_firestore::NUM_SNPS={number_of_cols}::{study_title}::{email}")
        print(f"Your data has {number_of_rows} rows and {number_of_cols} columns.")
    else:
        raise ValueError(f"Unknown study type: {study_type}")

    update_firestore(f"update_firestore::status=not ready::{study_title}::{email}")
    data_hash = checksumdir.dirhash(data_path, "md5")
    update_firestore(f"update_firestore::DATA_HASH={data_hash}::{study_title}::{email}")

    with open(os.path.join(constants.SFKIT_DIR, "data_path.txt"), "w") as f:
        if study_type == "SFGWAS":
            f.write(geno_binary_file_prefix + "\n")
        f.write(data_path + "\n")

    print("Successfully registered and validated data!")
    return True


def validate_geno_binary_file_prefix(geno_binary_file_prefix: str) -> str:
    if not geno_binary_file_prefix:
        geno_binary_file_prefix = input(
            f"Enter absolute path to geno binary file prefix (e.g. '/home/smendels/for_sfgwas/geno/lung_party1_chr%d'): "
        )  # sourcery skip: remove-redundant-fstring
    if geno_binary_file_prefix != "demo" and not os.path.isabs(geno_binary_file_prefix):
        print("I need an ABSOLUTE path for the geno_binary_file_prefix.")
        exit(1)
    return geno_binary_file_prefix


def validate_data_path(data_path: str) -> str:
    if not data_path:
        data_path = input("Enter the (absolute) path to your data files (e.g. /home/smendels/for_sfgwas): ")
    if data_path != "demo" and not os.path.isabs(data_path):
        print("I need an ABSOLUTE path for the data_path.")
        exit(1)
    return data_path


def validate_sfgwas_data(geno_binary_file_prefix: str, data_path: str) -> int:
    for suffix in ["pgen", "pvar", "psam"]:
        assert os.path.isfile(geno_binary_file_prefix % 1 + "." + suffix)

    rows = num_rows(os.path.join(data_path, "pheno.txt"))
    assert rows == num_rows(os.path.join(data_path, "cov.txt")), "pheno and cov have different number of rows"
    assert rows == num_rows(os.path.join(data_path, "sample_keep.txt")), "pheno and sample_keep differ in num-rows"
    return rows


def validate_mpcgwas_data(data_path: str) -> int:
    rows = num_rows(os.path.join(data_path, "cov.txt"))
    assert rows == num_rows(os.path.join(data_path, "geno.txt"))
    assert rows == num_rows(os.path.join(data_path, "pheno.txt"))
    return rows


def num_rows(file_path: str) -> int:
    return sum(1 for _ in open(file_path))


def num_cols(file_path: str) -> int:
    return len(open(file_path).readline().split())


def using_demo(study_title: str, email: str) -> bool:
    update_firestore(f"update_firestore::status=not ready::{study_title}::{email}")
    print("Using demo data!")
    print("Successfully registered and validated data!")
    return True
