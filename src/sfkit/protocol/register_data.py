import os

import checksumdir

from sfkit.api import get_doc_ref_dict, update_firestore
from sfkit.protocol.utils import constants
from sfkit.protocol.utils.helper_functions import authenticate_user
from sfkit.api import get_user_email


def register_data(geno_binary_file_prefix: str, data_path: str) -> bool:
    """
    Register data with the server and validate that the data formatting looks correct.
    """

    authenticate_user()

    doc_ref_dict: dict = get_doc_ref_dict()
    email: str = get_user_email()
    study_type: str = doc_ref_dict["study_type"]
    num_inds: int

    if study_type == "SFGWAS":
        geno_binary_file_prefix = validate_geno_binary_file_prefix(geno_binary_file_prefix)
        data_path = validate_data_path(data_path)

        if data_path == "demo":
            return using_demo()

        num_inds: int = validate_sfgwas_data(geno_binary_file_prefix, data_path)
        assert num_inds == int(doc_ref_dict["personal_parameters"][email]["NUM_INDS"]["value"])
        num_snps: int = num_rows(os.path.join(data_path, "snp_ids.txt"))
        assert num_snps == int(doc_ref_dict["personal_parameters"][email]["NUM_SNPS"]["value"])
        print(f"Your data has {num_inds} individuals and {num_snps} SNPs.")
    elif study_type == "MPCGWAS":
        data_path = validate_data_path(data_path)

        if data_path == "demo":
            return using_demo()

        num_inds: int = validate_mpcgwas_data(data_path)
        assert num_inds == int(doc_ref_dict["personal_parameters"][email]["NUM_INDS"]["value"])
        print(f"Your data has {num_inds} individuals.")
    elif study_type == "PCA":
        data_path = validate_data_path(data_path)

        if data_path == "demo":
            return using_demo()

        number_of_rows: int = num_rows(os.path.join(data_path, "data.txt"))
        assert number_of_rows == int(doc_ref_dict["personal_parameters"][email]["NUM_INDS"]["value"])
        number_of_cols: int = num_cols(os.path.join(data_path, "data.txt"))
        assert number_of_cols == int(doc_ref_dict["parameters"]["num_columns"]["value"])
        print(f"Your data has {number_of_rows} rows and {number_of_cols} columns.")
    else:
        raise ValueError(f"Unknown study type: {study_type}")

    update_firestore("update_firestore::status=not ready")
    data_hash = checksumdir.dirhash(data_path, "md5")
    update_firestore(f"update_firestore::DATA_HASH={data_hash}")

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


def using_demo() -> bool:
    update_firestore("update_firestore::status=not ready")
    print("Using demo data!")
    print("Successfully registered and validated data!")
    return True
