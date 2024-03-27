import os
from typing import Optional, Tuple

import checksumdir

from sfkit.api import get_doc_ref_dict, update_firestore
from sfkit.encryption.mpc.encrypt_data import encrypt_data
from sfkit.utils import constants
from sfkit.utils.helper_functions import authenticate_user, condition_or_fail
from sfkit.api import get_username, website_send_file


def register_data(geno_binary_file_prefix: str = "", data_path: str = "") -> bool:
    """
    Register data with the server and validate that the data formatting looks correct.
    """
    authenticate_user()

    doc_ref_dict: dict = get_doc_ref_dict()

    if doc_ref_dict.get("demo"):
        print("No validation: using demo data!")
        update_firestore("update_firestore::status=validated data")
        return True

    username: str = get_username()
    role: str = str(doc_ref_dict["participants"].index(username))
    study_type: str = doc_ref_dict["study_type"]

    validated = "validated" in doc_ref_dict["status"][username]
    if not validated:
        update_firestore("update_firestore::task=Validating Data Format")

        if study_type == "SF-GWAS":
            if constants.BLOCKS_MODE not in doc_ref_dict["description"]:
                geno_binary_file_prefix, data_path = validate_sfgwas(
                    doc_ref_dict, username, data_path, geno_binary_file_prefix
                )
        elif study_type == "MPC-GWAS":
            data_path = validate_mpcgwas(doc_ref_dict, username, data_path, role)
        elif study_type == "PCA":
            data_path = validate_pca(doc_ref_dict, username, data_path)
        elif study_type == "SF-RELATE":
            data_path = validate_sfrelate(doc_ref_dict, username, data_path, role)
        else:
            raise ValueError(f"Unknown study type: {study_type}")

        update_firestore("update_firestore::status=validated data")

        if constants.BLOCKS_MODE not in doc_ref_dict["description"]:
            data_hash = checksumdir.dirhash(data_path, "md5")
            update_firestore(f"update_firestore::DATA_HASH={data_hash}")

        with open(os.path.join(constants.SFKIT_DIR, "data_path.txt"), "w") as f:
            if study_type == "SF-GWAS":
                f.write(geno_binary_file_prefix + "\n")
            f.write(data_path + "\n")

        print("Successfully registered and validated data!")
    else:
        print("Data has already been validated; skipping validation step.")

    encrypt_mpcgwas(role, study_type)

    return True


def encrypt_mpcgwas(role: str, study_type: str) -> None:
    if study_type == "MPC-GWAS" and role in {"1", "2"}:
        print("Now encrypting data...")
        update_firestore("update_firestore::task=Encrypting data")
        try:
            encrypt_data()
        except Exception as e:
            condition_or_fail(False, f"encrypt_data::error={e}")


def validate_sfgwas(
    doc_ref_dict: dict, username: str, data_path: str, geno_binary_file_prefix: str
) -> Tuple[str, str]:
    geno_binary_file_prefix = validate_geno_binary_file_prefix(geno_binary_file_prefix)
    data_path = validate_data_path(data_path)

    if data_path == "demo" or (constants.IS_DOCKER and doc_ref_dict["demo"]):
        using_demo()

    num_inds_value = doc_ref_dict["personal_parameters"][username]["NUM_INDS"]["value"]
    num_snps_value = doc_ref_dict["parameters"]["num_snps"]["value"]

    if num_inds_value == "":
        condition_or_fail(False, "NUM_INDS is not set. Please set it and try again.")
    if num_snps_value == "":
        condition_or_fail(False, "num_snps is not set. Please set it and try again.")

    num_inds: int = validate_sfgwas_data(geno_binary_file_prefix, data_path)
    condition_or_fail(
        num_inds == int(num_inds_value),
        "NUM_INDS does not match the number of individuals in the data.",
    )
    num_snps: int = num_rows(os.path.join(data_path, "snp_ids.txt"))
    condition_or_fail(
        num_snps == int(num_snps_value),
        "num_snps does not match the number of SNPs in the data.",
    )
    print(f"Your data has {num_inds} individuals and {num_snps} SNPs.")

    return geno_binary_file_prefix, data_path


def validate_mpcgwas(doc_ref_dict: dict, username: str, data_path: str, role: str) -> str:
    data_path = validate_data_path(data_path)

    if data_path == "demo" or (constants.IS_DOCKER and doc_ref_dict["demo"]):
        using_demo()

    num_inds_value = doc_ref_dict["personal_parameters"][username]["NUM_INDS"]["value"]
    num_covs_value = doc_ref_dict["parameters"]["NUM_COVS"]["value"]

    if num_inds_value == "":
        condition_or_fail(False, "NUM_INDS is not set. Please set it and try again.")
    if num_covs_value == "":
        condition_or_fail(False, "NUM_COVS is not set. Please set it and try again.")

    num_inds, num_covs = validate_mpcgwas_data(data_path)
    condition_or_fail(
        num_inds == int(num_inds_value),
        "NUM_INDS does not match the number of individuals in the data.",
    )
    condition_or_fail(
        num_covs == int(num_covs_value),
        "NUM_COVS does not match the number of covariates in the data.",
    )

    print(f"Your data has {num_inds} individuals and {num_covs} covariates.")

    if role == "1":
        website_send_file(open(os.path.join(data_path, "pos.txt"), "r"), "pos.txt")

    return data_path


def validate_pca(doc_ref_dict: dict, username: str, data_path: str) -> str:
    data_path = validate_data_path(data_path)

    if data_path == "demo" or (constants.IS_DOCKER and doc_ref_dict["demo"]):
        using_demo()

    num_inds_value = doc_ref_dict["personal_parameters"][username]["NUM_INDS"]["value"]
    number_of_cols_value = doc_ref_dict["parameters"]["num_columns"]["value"]

    if num_inds_value == "":
        condition_or_fail(False, "NUM_INDS is not set. Please set it and try again.")
    if number_of_cols_value == "":
        condition_or_fail(False, "num_columns is not set. Please set it and try again.")

    number_of_rows: int = num_rows(os.path.join(data_path, "data.txt"))
    condition_or_fail(
        number_of_rows == int(num_inds_value),
        "NUM_INDS does not match the number of rows in the data.",
    )
    number_of_cols: int = num_cols(os.path.join(data_path, "data.txt"))
    condition_or_fail(
        number_of_cols == int(number_of_cols_value),
        "num_columns does not match the number of columns in the data.",
    )
    print(f"Your data has {number_of_rows} rows and {number_of_cols} columns.")

    return data_path


def validate_sfrelate(doc_ref_dict: dict, username: str, data_path: str, role: str) -> str:
    if data_path == "demo" or (constants.IS_DOCKER and doc_ref_dict["demo"]):
        using_demo()

    data_path = validate_data_path(data_path)

    # TODO: validate the data for SF-RELATE
    return data_path


def validate_geno_binary_file_prefix(geno_binary_file_prefix: str) -> str:
    if not geno_binary_file_prefix:
        if constants.IS_DOCKER and os.path.exists("/app/data/geno"):
            geno_binary_file_prefix = f"/app/data/geno/ch%d"
            print(f"Using default geno_binary_file_prefix for docker: {geno_binary_file_prefix}")
        else:
            geno_binary_file_prefix = input(
                f"Enter absolute path to geno binary file prefix (e.g. '/home/username/for_sfgwas/geno/ch%d'): "
            )  # sourcery skip: remove-redundant-fstring
    if geno_binary_file_prefix != "demo" and not os.path.isabs(geno_binary_file_prefix):
        print("I need an ABSOLUTE path for the geno_binary_file_prefix.")
        exit(1)
    return geno_binary_file_prefix


def validate_data_path(data_path: str) -> str:
    if not data_path:
        if constants.IS_DOCKER and os.path.exists("/app/data"):
            data_path = "/app/data"
            print(f"Using default data_path for docker: {data_path}")
        else:
            data_path = input("Enter the (absolute) path to your data files (e.g. /home/username/for_sfgwas): ")
    if data_path != "demo" and not os.path.isabs(data_path):
        print("I need an ABSOLUTE path for the data_path.")
        exit(1)
    return data_path


def validate_sfgwas_data(geno_binary_file_prefix: str, data_path: str) -> int:
    for suffix in ["pgen", "pvar", "psam"]:
        condition_or_fail(
            os.path.isfile(geno_binary_file_prefix % 1 + "." + suffix),
            f"Could not find {geno_binary_file_prefix % 1}.{suffix} file.",
        )

    rows: int = num_rows(os.path.join(data_path, "pheno.txt"))
    condition_or_fail(
        rows == num_rows(os.path.join(data_path, "cov.txt")), "pheno and cov have different number of rows"
    )
    condition_or_fail(
        rows == num_rows(os.path.join(data_path, "sample_keep.txt")), "pheno and sample_keep differ in num-rows"
    )

    duplicate_line = find_duplicate_line(os.path.join(data_path, "snp_ids.txt"))
    condition_or_fail(duplicate_line is None, f"snp_ids.txt has duplicate line: {duplicate_line}")

    return rows


def validate_mpcgwas_data(data_path: str) -> Tuple[int, int]:
    rows = num_rows(os.path.join(data_path, "cov.txt"))
    condition_or_fail(
        rows == num_rows(os.path.join(data_path, "geno.txt")), "cov and geno have different number of rows"
    )
    condition_or_fail(
        rows == num_rows(os.path.join(data_path, "pheno.txt")), "cov and pheno have different number of rows"
    )
    num_covs = num_cols(os.path.join(data_path, "cov.txt"))

    duplicate_line = find_duplicate_line(os.path.join(data_path, "pos.txt"))
    condition_or_fail(duplicate_line is None, f"pos.txt has duplicate line: {duplicate_line}")

    return rows, num_covs


def num_rows(file_path: str) -> int:
    return sum(1 for _ in open(file_path))


def num_cols(file_path: str) -> int:
    return len(open(file_path).readline().split())


def using_demo() -> None:
    update_firestore("update_firestore::status=validated data")
    print("Using demo data!")
    print("Successfully registered and validated data!")
    exit(0)


def find_duplicate_line(filename: str) -> Optional[str]:
    with open(filename, "r") as file:
        prev_line = None
        for line in file:
            if prev_line and line.strip() == prev_line.strip():
                return prev_line.strip()
            prev_line = line
    return None
