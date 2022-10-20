"""
Run the PCA protocol
"""
import os

import toml
from sfkit.api import get_doc_ref_dict
from sfkit.protocol.utils import constants
from sfkit.protocol.utils.sfgwas_protocol import (
    build_sfgwas,
    generate_shared_keys,
    install_sfgwas,
    start_sfgwas,
    update_sfgwas_go,
)


def run_pca_protocol(role: str) -> None:
    install_sfgwas()
    generate_shared_keys(int(role))
    print("Begin updating config files")
    update_config_party(role)
    update_config_global()
    update_sfgwas_go("pca")
    build_sfgwas()
    start_sfgwas(role, protocol="PCA")


def update_config_party(role: str) -> None:
    """
    Update configLocal.Party{role}.toml
    :param role: 0, 1, 2
    """
    config_file_path = f"sfgwas/config/pca/configLocal.Party{role}.toml"
    data = toml.load(config_file_path)

    if role != "0":
        with open(os.path.join(constants.SFKIT_DIR, "data_path.txt"), "r") as f:
            data_path = f.readline().rstrip()

        data["geno_file"] = f"{data_path}/geno.txt"

    data["shared_keys_path"] = constants.SFKIT_DIR

    with open(config_file_path, "w") as f:
        toml.dump(data, f)


def update_config_global() -> None:
    """
    Update configGlobal.toml
    """
    doc_ref_dict: dict = get_doc_ref_dict()
    config_file_path = "sfgwas/config/pca/configGlobal.toml"
    data = toml.load(config_file_path)

    print("Updating NUM_INDS/num_rows and NUM_SNPS/num_columns")
    for i, participant in enumerate(doc_ref_dict["participants"]):
        data["num_rows"][i] = int(doc_ref_dict["personal_parameters"][participant]["NUM_INDS"]["value"])
        print("num_rows for", participant, "is", data["num_rows"][i])
        assert i == 0 or data["num_rows"][i] > 0, "num_rows must be greater than 0"
    data["num_columns"] = int(doc_ref_dict["parameters"]["NUM_SNPS"]["value"])
    print("num_columns is", data["num_columns"])
    assert data["num_columns"] > 0, "num_columns must be greater than 0"

    # Update the ip addresses and ports
    for i, participant in enumerate(doc_ref_dict["participants"]):
        ip_addr = doc_ref_dict["personal_parameters"][participant]["IP_ADDRESS"]["value"]
        data["servers"][f"party{i}"]["ipaddr"] = ip_addr

    _, p1, p2 = doc_ref_dict["personal_parameters"][doc_ref_dict["participants"][0]]["PORTS"]["value"].split(",")
    data["servers"]["party0"]["ports"]["party1"] = p1
    data["servers"]["party0"]["ports"]["party2"] = p2

    _, _, p2 = doc_ref_dict["personal_parameters"][doc_ref_dict["participants"][1]]["PORTS"]["value"].split(",")
    data["servers"]["party1"]["ports"]["party2"] = p2

    with open(config_file_path, "w") as f:
        toml.dump(data, f)
