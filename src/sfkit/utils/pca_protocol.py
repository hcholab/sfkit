"""
Run the PCA protocol
"""
import os
import shutil

import toml

from sfkit.utils import constants
from sfkit.utils.sfgwas_protocol import (
    build_sfgwas,
    generate_shared_keys,
    install_sfgwas,
    start_sfgwas,
    update_config_global,
    update_sfgwas_go,
)


def run_pca_protocol(role: str) -> None:
    install_sfgwas()
    generate_shared_keys(int(role))
    print("Begin updating config files")
    update_config_local(role)
    update_config_global(protocol="pca")
    update_sfgwas_go("pca")
    build_sfgwas()
    start_sfgwas(role, protocol="PCA")


def update_config_local(role: str) -> None:
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
