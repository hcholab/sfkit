"""
Run the PCA protocol
"""
import os
import shutil

import tomlkit

from sfkit.utils import constants
from sfkit.utils.sfgwas_protocol import (
    build_sfgwas,
    generate_shared_keys,
    install_sfgwas,
    start_sfgwas,
    sync_with_other_vms,
    update_config_global,
)


def run_pca_protocol(role: str, demo: bool = False) -> None:
    if not (constants.IS_DOCKER or constants.IS_INSTALLED_VIA_SCRIPT):
        install_sfgwas()
    if not demo:
        generate_shared_keys(int(role))
        print("Begin updating config files")
        update_config_local(role)
        update_config_global(protocol="pca")
    if not (constants.IS_DOCKER or constants.IS_INSTALLED_VIA_SCRIPT):
        build_sfgwas()
    sync_with_other_vms(role, demo)
    start_sfgwas(role, demo, protocol="pca")


def update_config_local(role: str) -> None:
    """
    Update configLocal.Party{role}.toml
    :param role: 0, 1, 2, ...
    """
    config_file_path = f"{constants.EXECUTABLES_PREFIX}sfgwas/config/pca/configLocal.Party{role}.toml"

    try:
        with open(config_file_path, "r") as f:
            data = tomlkit.parse(f.read())
    except FileNotFoundError:
        print(f"File {config_file_path} not found.")
        print("Creating it...")
        shutil.copyfile(f"{constants.EXECUTABLES_PREFIX}sfgwas/config/pca/configLocal.Party2.toml", config_file_path)
        with open(config_file_path, "r") as f:
            data = tomlkit.parse(f.read())

    if role != "0":
        with open(os.path.join(constants.SFKIT_DIR, "data_path.txt"), "r") as f:
            data_path = f.readline().rstrip()

        data["input_file"] = f"{data_path}/data.txt"

    data["shared_keys_path"] = constants.SFKIT_DIR
    data["output_dir"] = f"out/party{role}"
    data["cache_dir"] = f"cache/party{role}"

    with open(config_file_path, "w") as f:
        f.write(tomlkit.dumps(data))
