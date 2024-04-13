"""
Run the sfgwas protocol
"""

import copy
import fileinput
import os
import random
import shutil
import threading
import time

import tomlkit
from nacl.encoding import HexEncoder
from nacl.public import Box, PrivateKey, PublicKey

from sfkit.api import get_doc_ref_dict, update_firestore
from sfkit.utils import constants
from sfkit.utils.helper_functions import (
    condition_or_fail,
    install_go,
    run_command,
)
from sfkit.utils.sfgwas_helper_functions import (
    boot_sfkit_proxy,
    get_file_paths,
    post_process_results,
    run_sfprotocol_with_task_updates,
    to_float_int_or_bool,
    use_existing_config,
)


def run_sfgwas_protocol(role: str, phase: str = "", demo: bool = False) -> None:
    """
    Run the sfgwas protocol
    :param role: 0, 1, 2, ...
    :param phase: "", "1", "2", "3"
    :param demo: True or False
    """
    if not (constants.IS_DOCKER or constants.IS_INSTALLED_VIA_SCRIPT):
        install_sfgwas()
    if not demo:
        generate_shared_keys(int(role))
        print("Begin updating config files")
        update_config_local(role)
        update_config_global()
    update_config_global_phase(phase, demo)
    if not (constants.IS_DOCKER or constants.IS_INSTALLED_VIA_SCRIPT):
        build_sfgwas()
    sync_with_other_vms(role, demo)
    start_sfgwas(role, demo)


def install_sfgwas() -> None:
    """
    Install sfgwas and its dependencies
    """
    update_firestore("update_firestore::task=Installing dependencies")
    print("Begin installing dependencies")

    plink2_download_link = "https://s3.amazonaws.com/plink2-assets/plink2_linux_avx2_latest.zip"
    plink2_zip_file = plink2_download_link.split("/")[-1]

    run_command(["sudo", "apt-get", "update", "-y"])
    run_command(["sudo", "apt-get", "install", "wget", "git", "zip", "unzip", "snapd", "-y"])

    install_go()

    run_command(["wget", "-nc", plink2_download_link])
    run_command(["sudo", "unzip", "-o", plink2_zip_file, "-d", "/usr/local/bin"])
    run_command(["pip3", "install", "numpy"])

    # make sure plink2 successfully installed
    condition_or_fail(
        os.path.isfile("/usr/local/bin/plink2"),
        "plink2 not installed (probably need to get new version)",
    )

    if os.path.isdir("lattigo"):
        print("lattigo already exists")
    else:
        print("Installing lattigo")
        run_command(["git", "clone", "https://github.com/hcholab/lattigo"])
        os.chdir("lattigo")
        run_command(["git", "switch", "lattigo_pca"])
        os.chdir("..")

    if os.path.isdir("mpc-core"):
        print("mpc-core already exists")
    else:
        print("Installing mpc-core")
        run_command(["git", "clone", "https://github.com/hhcho/mpc-core"])

    if os.path.isdir("sfgwas"):
        print("sfgwas already exists")
    else:
        print("Installing sfgwas")
        run_command(["git", "clone", "https://github.com/hcholab/sfgwas"])

    print("Finished installing dependencies")


def generate_shared_keys(role: int, skip_cp0: bool = False) -> None:
    """
    Generate shared keys for the sfgwas protocol
    :param role: 0, 1, 2, ...
    """
    doc_ref_dict: dict = get_doc_ref_dict()
    update_firestore("update_firestore::task=Generating cryptographic keys")
    print("Generating shared keys...")

    private_key_path = os.path.join(constants.SFKIT_DIR, "my_private_key.txt")
    with open(private_key_path, "r") as f:
        my_private_key = PrivateKey(f.readline().rstrip().encode(), encoder=HexEncoder)

    for i, other_username in enumerate(doc_ref_dict["participants"]):
        if i == role:
            continue
        if skip_cp0 and i == 0:
            continue
        other_public_key_str: str = doc_ref_dict["personal_parameters"][other_username]["PUBLIC_KEY"]["value"]
        while not other_public_key_str:
            if i == 0:  # Broad/cp0
                print("Waiting for the Broad (CP0) to set up...")
            else:
                print(f"No public key found for {other_username}.  Waiting...")
            time.sleep(5)
            doc_ref_dict = get_doc_ref_dict()
            other_public_key_str = doc_ref_dict["personal_parameters"][other_username]["PUBLIC_KEY"]["value"]
        other_public_key = PublicKey(other_public_key_str.encode(), encoder=HexEncoder)
        condition_or_fail(my_private_key != other_public_key, "Private and public keys must be different")
        shared_key = Box(my_private_key, other_public_key).shared_key()
        shared_key_path = os.path.join(constants.SFKIT_DIR, f"shared_key_{min(role, i)}_{max(role, i)}.bin")
        with open(shared_key_path, "wb") as f:
            f.write(shared_key)

    if skip_cp0:
        with open(os.path.join(constants.SFKIT_DIR, "shared_key_0_1.bin"), "wb") as f:
            f.write(constants.DUMMY_KEY_01)
        with open(os.path.join(constants.SFKIT_DIR, "shared_key_0_2.bin"), "wb") as f:
            f.write(constants.DUMMY_KEY_02)

    cp0: str = doc_ref_dict["participants"][0]
    random.seed(doc_ref_dict["personal_parameters"][cp0]["PUBLIC_KEY"]["value"])
    global_shared_key = random.getrandbits(256).to_bytes(32, "big")
    with open(os.path.join(constants.SFKIT_DIR, "shared_key_global.bin"), "wb") as f:
        f.write(global_shared_key)

    print(f"Shared keys generated and saved to {constants.SFKIT_DIR}.")


def update_config_local(role: str, protocol: str = "gwas") -> None:
    """
    Update configLocal.Party{role}.toml
    :param role: 0, 1, 2, ...
    """
    doc_ref_dict: dict = get_doc_ref_dict()
    if constants.BLOCKS_MODE in doc_ref_dict["description"]:
        use_existing_config(role, doc_ref_dict)
        return

    config_file_path = f"{constants.EXECUTABLES_PREFIX}sfgwas/config/{protocol}/configLocal.Party{role}.toml"

    try:
        with open(config_file_path, "r") as f:
            data = tomlkit.parse(f.read())

    except FileNotFoundError:
        print(f"File {config_file_path} not found.")
        print("Creating it...")
        shutil.copyfile(
            f"{constants.EXECUTABLES_PREFIX}sfgwas/config/{protocol}/configLocal.Party2.toml", config_file_path
        )
        with open(config_file_path, "r") as f:
            data = tomlkit.parse(f.read())

    if role != "0":
        update_data_file_paths(data)
    data["shared_keys_path"] = constants.SFKIT_DIR
    data["output_dir"] = f"out/party{role}"
    data["cache_dir"] = f"cache/party{role}"

    doc_ref_dict = get_doc_ref_dict()
    user_id: str = doc_ref_dict["participants"][int(role)]
    data["local_num_threads"] = int(doc_ref_dict["personal_parameters"][user_id]["NUM_CPUS"]["value"])
    data["assoc_num_blocks_parallel"] = int(data.get("local_num_threads", 16)) // 8
    data["memory_limit"] = int(int(data.get("local_num_threads", 16)) * 8 * 1_000_000_000)

    with open(config_file_path, "w") as f:
        f.write(tomlkit.dumps(data))


def update_data_file_paths(data: dict) -> None:
    geno_file_prefix, data_path = get_file_paths()

    data["geno_binary_file_prefix"] = f"{geno_file_prefix}"
    data["geno_block_size_file"] = f"{data_path}/chrom_sizes.txt"
    data["pheno_file"] = f"{data_path}/pheno.txt"
    data["covar_file"] = f"{data_path}/cov.txt"
    data["snp_position_file"] = f"{data_path}/snp_pos.txt"
    data["sample_keep_file"] = f"{data_path}/sample_keep.txt"
    data["snp_ids_file"] = f"{data_path}/snp_ids.txt"
    data["geno_count_file"] = f"{data_path}/all.gcount.transpose.bin"

    # don't need to return anything because data is a mutable object


def update_config_global(protocol: str = "gwas") -> None:
    """
    Update configGlobal.toml
    """
    print("Updating configGlobal.toml")
    doc_ref_dict: dict = get_doc_ref_dict()
    config_file_path = f"{constants.EXECUTABLES_PREFIX}sfgwas/config/{protocol}/configGlobal.toml"
    with open(config_file_path, "r") as f:
        data = tomlkit.parse(f.read())

    # Update the ip addresses and ports
    for i, participant in enumerate(doc_ref_dict["participants"]):
        if f"party{i}" not in data.get("servers", {}):
            data.get("servers", {})[f"party{i}"] = copy.deepcopy(data.get("servers", {})[f"party{i-1}"])

        ip_addr = doc_ref_dict["personal_parameters"][participant]["IP_ADDRESS"]["value"]
        data.get("servers", {}).get(f"party{i}", {})["ipaddr"] = "127.0.0.1" if constants.SFKIT_PROXY_ON else ip_addr

        ports: list = doc_ref_dict["personal_parameters"][participant]["PORTS"]["value"].split(",")
        for j, port in enumerate(ports):
            if port != "null" and i != j:
                data.get("servers", {}).get(f"party{i}", {}).get("ports", {})[f"party{j}"] = port

    if constants.BLOCKS_MODE not in doc_ref_dict["description"]:
        data["num_main_parties"] = len(doc_ref_dict["participants"]) - 1

        row_name = "num_rows" if protocol == "pca" else "num_inds"
        col_name = "num_columns" if protocol == "pca" else "num_snps"
        data[row_name] = []
        for i, participant in enumerate(doc_ref_dict["participants"]):
            data.get(row_name, []).append(int(doc_ref_dict["personal_parameters"][participant]["NUM_INDS"]["value"]))
            print(f"{row_name} for {participant} is {data.get(row_name, [])[i]}")
            condition_or_fail(i == 0 or data.get(row_name, [])[i] > 0, f"{row_name} must be greater than 0")
        data[col_name] = (
            int(doc_ref_dict["parameters"]["num_snps"]["value"])
            if protocol == "gwas"
            else int(doc_ref_dict["parameters"]["num_columns"]["value"])
        )
        print(f"{col_name} is {data[col_name]}")
        condition_or_fail(data.get(col_name, 0) > 0, f"{col_name} must be greater than 0")

        # shared and advanced parameters
        pars = {**doc_ref_dict["parameters"], **doc_ref_dict["advanced_parameters"]}
        for key, value in pars.items():
            if key in data:
                data[key] = to_float_int_or_bool(value["value"])

    with open(config_file_path, "w") as f:
        f.write(tomlkit.dumps(data))


def update_config_global_phase(phase: str, demo: bool, protocol: str = "gwas") -> None:
    """
    Update based on phase in configGlobal.toml
    :param phase: "1", "2", "3"
    """
    config_file_path = f"{constants.EXECUTABLES_PREFIX}sfgwas/config/{protocol}/configGlobal.toml"
    with open(config_file_path, "r") as f:
        data = tomlkit.parse(f.read())

    data["phase"] = phase
    if phase == "2":
        data["use_cached_qc"] = True
    elif phase == "3":
        data["use_cached_qc"] = True
        data["use_cached_pca"] = True

    if demo:
        data["num_power_iters"] = 2
        data["iter_per_eigenval"] = 2
        data["num_pcs_to_remove"] = 2

    with open(config_file_path, "w") as f:
        f.write(tomlkit.dumps(data))


def update_sfgwas_go(protocol: str = "gwas") -> None:
    """
    Update sfgwas.go
    """
    for line in fileinput.input(f"{constants.EXECUTABLES_PREFIX}sfgwas/sfgwas.go", inplace=True):
        if "CONFIG_PATH = " in line:
            print(f'var CONFIG_PATH = "config/{protocol}"')
        else:
            print(line, end="")


def build_sfgwas() -> None:
    """
    build/compile sfgwas
    """
    update_firestore("update_firestore::task=Compiling code")
    print("Building sfgwas code")

    if "/usr/local/go/bin" not in os.environ["PATH"]:
        os.environ["PATH"] += f"{os.pathsep}/usr/local/go/bin"
    os.environ["HOME"] = os.path.expanduser("~")
    os.environ["GOCACHE"] = os.path.join(os.environ["HOME"], ".cache", "go-build")
    os.chdir("sfgwas")

    run_command(["go", "get", "-t", "github.com/hcholab/sfgwas"])
    run_command(["go", "build"])

    os.chdir("..")

    print("Finished building sfgwas code")


def sync_with_other_vms(role: str, demo: bool, skip_cp0: bool = False) -> None:
    update_firestore("update_firestore::status=syncing up")
    update_firestore("update_firestore::task=Syncing up machines")
    print("Begin syncing up")

    if demo:
        print("Skipping sync for demo")
        return

    while True:
        doc_ref_dict: dict = get_doc_ref_dict()
        statuses: dict = doc_ref_dict["status"]
        if skip_cp0:
            statuses.pop("Broad", None)
        if all(status == "syncing up" for status in statuses.values()):
            break
        print("Waiting for all participants to sync up...")
        time.sleep(5)
    time.sleep(15 * int(role))
    print("Finished syncing up")


def start_sfgwas(role: str, demo: bool = False, protocol: str = "gwas") -> None:
    """
    Start the actual sfgwas program
    :param role: 0, 1, 2, ...
    :param demo: True if running demo
    """
    update_firestore("update_firestore::task=Initiating Protocol")
    print("Begin SF-GWAS protocol")

    if constants.SFKIT_PROXY_ON:
        boot_sfkit_proxy(role=role, protocol=protocol)
        os.environ["ALL_PROXY"] = "socks5://localhost:8000"

    os.chdir(f"{constants.EXECUTABLES_PREFIX}sfgwas")

    if demo and (constants.IS_DOCKER or constants.IS_INSTALLED_VIA_SCRIPT):
        threads = []
        for r in range(3):
            thread = threading.Thread(target=run_sfprotocol_with_task_updates, args=(["sfgwas"], protocol, str(r)))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()
    elif demo:
        run_sfprotocol_with_task_updates(["bash", "run_example.sh"], protocol, role)
    elif constants.IS_DOCKER or constants.IS_INSTALLED_VIA_SCRIPT:
        run_sfprotocol_with_task_updates(["sfgwas"], protocol, role)
    else:
        run_sfprotocol_with_task_updates(["go", "run", "sfgwas.go"], protocol, role)

    print(f"Finished {protocol} protocol")

    if role == "0":
        update_firestore("update_firestore::status=Finished protocol!")
        return

    post_process_results(role, demo, protocol)
