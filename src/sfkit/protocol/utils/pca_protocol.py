"""
Run the PCA protocol
"""
import os

import toml
from sfkit.protocol.utils import constants
from sfkit.protocol.utils.sfgwas_protocol import (
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
    update_config_party(role)
    update_config_global("pca/")
    update_sfgwas_go("pca")
    build_sfgwas()
    start_sfgwas(role)


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
