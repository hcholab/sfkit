"""
Run the PCA protocol
"""
import copy
import os
import shutil

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
    :param role: 0, 1, 2, ...
    """
    config_file_path = f"sfgwas/config/pca/configLocal.Party{role}.toml"

    try:
        data = toml.load(config_file_path)
    except FileNotFoundError:
        print(f"File {config_file_path} not found.")
        print("Creating it...")
        shutil.copyfile("sfgwas/config/pca/configLocal.Party2.toml", config_file_path)
        data = toml.load(config_file_path)

    if role != "0":
        with open(os.path.join(constants.SFKIT_DIR, "data_path.txt"), "r") as f:
            data_path = f.readline().rstrip()

        data["input_file"] = f"{data_path}/data.txt"

    data["shared_keys_path"] = constants.SFKIT_DIR
    data["output_dir"] = f"out/party{role}"
    data["cache_dir"] = f"cache/party{role}"

    with open(config_file_path, "w") as f:
        toml.dump(data, f)


def update_config_global() -> None:
    """
    Update configGlobal.toml
    """
    doc_ref_dict: dict = get_doc_ref_dict()
    config_file_path = "sfgwas/config/pca/configGlobal.toml"
    data = toml.load(config_file_path)

    data["num_main_parties"] = len(doc_ref_dict["participants"]) - 1

    print("Updating NUM_INDS/num_rows and NUM_SNPS/num_columns")
    data["num_rows"] = []
    for i, participant in enumerate(doc_ref_dict["participants"]):
        data["num_rows"].append(int(doc_ref_dict["personal_parameters"][participant]["NUM_INDS"]["value"]))
        print("num_rows for", participant, "is", data["num_rows"][i])
        assert i == 0 or data["num_rows"][i] > 0, "num_rows must be greater than 0"
    data["num_columns"] = int(doc_ref_dict["parameters"]["num_columns"]["value"])
    print("num_columns is", data["num_columns"])
    assert data["num_columns"] > 0, "num_columns must be greater than 0"

    # Update the ip addresses and ports
    for i, participant in enumerate(doc_ref_dict["participants"]):
        if f"party{i}" not in data["servers"]:
            data["servers"][f"party{i}"] = copy.deepcopy(data["servers"][f"party{i-1}"])

        ip_addr = doc_ref_dict["personal_parameters"][participant]["IP_ADDRESS"]["value"]
        data["servers"][f"party{i}"]["ipaddr"] = ip_addr

        ports: list = doc_ref_dict["personal_parameters"][participant]["PORTS"]["value"].split(",")
        for j, port in enumerate(ports):
            data["servers"][f"party{i}"]["ports"][f"party{j}"] = port

    with open(config_file_path, "w") as f:
        toml.dump(data, f)
