"""
Run the sfgwas protocol
"""

import copy
import fileinput
import os
import random
import shutil
import time
from typing import Union

import toml
from nacl.encoding import HexEncoder
from nacl.public import Box, PrivateKey, PublicKey

from sfkit.api import get_doc_ref_dict, update_firestore, website_send_file
from sfkit.utils import constants
from sfkit.utils.helper_functions import (
    condition_or_fail,
    copy_results_to_cloud_storage,
    plot_assoc,
    postprocess_assoc,
    run_command,
)


def run_sfgwas_protocol(role: str, phase: str = "", demo: bool = False) -> None:
    """
    Run the sfgwas protocol
    :param role: 0, 1, 2, ...
    :param phase: "", "1", "2", "3"
    :param demo: True or False
    """
    install_sfgwas()
    if not demo:
        generate_shared_keys(int(role))
        print("Begin updating config files")
        update_config_local(role)
        update_config_global()
    update_config_global_phase(phase, demo)
    update_sfgwas_go("gwas")
    build_sfgwas()
    start_sfgwas(role, demo)


def install_sfgwas() -> None:
    """
    Install sfgwas and its dependencies
    """
    update_firestore("update_firestore::task=Installing dependencies")
    print("Begin installing dependencies")
    commands = [
        "sudo apt-get update -y",
        "sudo apt-get install wget git zip unzip -y",
        "wget -nc https://golang.org/dl/go1.18.1.linux-amd64.tar.gz",
        "sudo rm -rf /usr/local/go && sudo tar -C /usr/local -xzf go1.18.1.linux-amd64.tar.gz",
        "wget -nc https://s3.amazonaws.com/plink2-assets/alpha3/plink2_linux_avx2_20220603.zip",
        "mkdir -p ~/.local/bin",
        "unzip -o plink2_linux_avx2_20220603.zip -d ~/.local/bin",
        "pip3 install numpy",
    ]
    for command in commands:
        run_command(command)

    if os.path.isdir("lattigo"):
        print("lattigo already exists")
    else:
        print("Installing lattigo")
        run_command("git clone https://github.com/hcholab/lattigo && cd lattigo && git switch lattigo_pca")

    if os.path.isdir("mpc-core"):
        print("mpc-core already exists")
    else:
        print("Installing mpc-core")
        run_command("git clone https://github.com/hhcho/mpc-core")

    if os.path.isdir("sfgwas"):
        print("sfgwas already exists")
    else:
        print("Installing sfgwas")
        run_command("git clone https://github.com/simonjmendelsohn/sfgwas && cd sfgwas")

    print("Finished installing dependencies")
    update_firestore("update_firestore::task=Installing dependencies completed")


def generate_shared_keys(role: int) -> None:
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
        other_public_key_str: str = doc_ref_dict["personal_parameters"][other_username]["PUBLIC_KEY"]["value"]
        while not other_public_key_str:
            if other_username == "Broad":
                print("Waiting for the Broad (CP0) to set up...")
            else:
                print(f"No public key found for {other_username}.  Waiting...")
            time.sleep(5)
            doc_ref_dict: dict = get_doc_ref_dict()
            other_public_key_str: str = doc_ref_dict["personal_parameters"][other_username]["PUBLIC_KEY"]["value"]
        other_public_key = PublicKey(other_public_key_str.encode(), encoder=HexEncoder)
        condition_or_fail(my_private_key != other_public_key, "Private and public keys must be different")
        shared_key = Box(my_private_key, other_public_key).shared_key()
        shared_key_path = os.path.join(constants.SFKIT_DIR, f"shared_key_{min(role, i)}_{max(role, i)}.bin")
        with open(shared_key_path, "wb") as f:
            f.write(shared_key)

    random.seed(doc_ref_dict["personal_parameters"]["Broad"]["PUBLIC_KEY"]["value"])
    global_shared_key = random.getrandbits(256).to_bytes(32, "big")
    with open(os.path.join(constants.SFKIT_DIR, "shared_key_global.bin"), "wb") as f:
        f.write(global_shared_key)

    print(f"Shared keys generated and saved to {constants.SFKIT_DIR}.")
    update_firestore("update_firestore::task=Generating cryptographic keys completed")


def update_config_local(role: str, protocol: str = "gwas") -> None:
    """
    Update configLocal.Party{role}.toml
    :param role: 0, 1, 2, ...
    """
    config_file_path = f"sfgwas/config/{protocol}/configLocal.Party{role}.toml"

    try:
        data: dict = toml.load(config_file_path)
    except FileNotFoundError:
        print(f"File {config_file_path} not found.")
        print("Creating it...")
        shutil.copyfile(f"sfgwas/config/{protocol}/configLocal.Party2.toml", config_file_path)
        data = toml.load(config_file_path)

    if role != "0":
        update_data_file_paths(data)
    data["shared_keys_path"] = constants.SFKIT_DIR
    data["output_dir"] = f"out/party{role}"
    data["cache_dir"] = f"cache/party{role}"

    with open(config_file_path, "w") as f:
        toml.dump(data, f)


def update_data_file_paths(data: dict) -> None:
    with open(os.path.join(constants.SFKIT_DIR, "data_path.txt"), "r") as f:
        geno_file_prefix = f.readline().rstrip()
        data_path = f.readline().rstrip()

    data["geno_binary_file_prefix"] = f"{geno_file_prefix}"
    data["geno_block_size_file"] = f"{data_path}/chrom_sizes.txt"
    data["pheno_file"] = f"{data_path}/pheno.txt"
    data["covar_file"] = f"{data_path}/cov.txt"
    data["snp_position_file"] = f"{data_path}/snp_pos.txt"
    data["sample_keep_file"] = f"{data_path}/sample_keep.txt"
    data["snp_ids_file"] = f"{data_path}/snp_ids.txt"
    data["geno_count_file"] = f"{data_path}/all.gcount.transpose.bin"


def update_config_global(protocol: str = "gwas") -> None:
    """
    Update configGlobal.toml
    """
    print("Updating configGlobal.toml")
    doc_ref_dict: dict = get_doc_ref_dict()
    config_file_path = f"sfgwas/config/{protocol}/configGlobal.toml"
    data = toml.load(config_file_path)

    data["num_main_parties"] = len(doc_ref_dict["participants"]) - 1

    row_name = "num_rows" if protocol == "pca" else "num_inds"
    col_name = "num_columns" if protocol == "pca" else "num_snps"
    data[row_name] = []
    for i, participant in enumerate(doc_ref_dict["participants"]):
        data[row_name].append(int(doc_ref_dict["personal_parameters"][participant]["NUM_INDS"]["value"]))
        print(f"{row_name} for {participant} is {data[row_name][i]}")
        condition_or_fail(i == 0 or data[row_name][i] > 0, f"{row_name} must be greater than 0")
    data[col_name] = (
        int(doc_ref_dict["parameters"]["num_snps"]["value"])
        if protocol == "gwas"
        else int(doc_ref_dict["parameters"]["num_columns"]["value"])
    )
    print(f"{col_name} is {data[col_name]}")
    condition_or_fail(data[col_name] > 0, f"{col_name} must be greater than 0")

    # Update the ip addresses and ports
    for i, participant in enumerate(doc_ref_dict["participants"]):
        if f"party{i}" not in data["servers"]:
            data["servers"][f"party{i}"] = copy.deepcopy(data["servers"][f"party{i-1}"])

        ip_addr = doc_ref_dict["personal_parameters"][participant]["IP_ADDRESS"]["value"]
        data["servers"][f"party{i}"]["ipaddr"] = ip_addr

        ports: list = doc_ref_dict["personal_parameters"][participant]["PORTS"]["value"].split(",")
        for j, port in enumerate(ports):
            data["servers"][f"party{i}"]["ports"][f"party{j}"] = port

    # shared and advanced parameters
    pars = doc_ref_dict["parameters"] | doc_ref_dict["advanced_parameters"]
    for key, value in pars.items():
        if key in data:
            data[key] = to_float_int_or_bool(value["value"])

    with open(config_file_path, "w") as f:
        toml.dump(data, f)


def update_config_global_phase(phase: str, demo: bool, protocol: str = "gwas") -> None:
    """
    Update based on phase in configGlobal.toml
    :param phase: "1", "2", "3"
    """
    config_file_path = f"sfgwas/config/{protocol}/configGlobal.toml"
    data = toml.load(config_file_path)

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
        toml.dump(data, f)


def update_sfgwas_go(protocol: str = "gwas") -> None:
    """
    Update sfgwas.go
    """
    for line in fileinput.input("sfgwas/sfgwas.go", inplace=True):
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
    command = """export PYTHONUNBUFFERED=TRUE && export PATH=$PATH:/usr/local/go/bin && export HOME=~ && export GOCACHE=~/.cache/go-build && cd sfgwas && go get -t github.com/simonjmendelsohn/sfgwas && go build"""
    run_command(command)
    print("Finished building sfgwas code")
    update_firestore("update_firestore::task=Compiling code completed")


def start_sfgwas(role: str, demo: bool = False, protocol: str = "SFGWAS") -> None:
    """
    Start the actual sfgwas program
    :param role: 0, 1, 2, ...
    :param demo: True if running demo
    """
    update_firestore(f"update_firestore::task=Running {protocol} protocol")
    print("Begin SFGWAS protocol")
    protocol_command = f"export PID={role} && go run sfgwas.go | tee stdout_party{role}.txt"
    if demo:
        protocol_command = "bash run_example.sh"
    command = f"export PYTHONUNBUFFERED=TRUE && export PATH=$PATH:/usr/local/go/bin && export HOME=~ && export GOCACHE=~/.cache/go-build && cd sfgwas && {protocol_command}"
    run_command(command, fail_message=f"Failed {protocol} protocol")
    print(f"Finished {protocol} protocol")

    doc_ref_dict: dict = get_doc_ref_dict()
    user_id: str = doc_ref_dict["participants"][int(role)]
    send_results: str = doc_ref_dict["personal_parameters"][user_id].get("SEND_RESULTS", {}).get("value")

    if protocol == "SFGWAS":
        make_new_assoc_and_manhattan_plot(doc_ref_dict, demo, role)
    # copy results to cloud storage
    if doc_ref_dict["setup_configuration"] == "website":
        data_path = doc_ref_dict["personal_parameters"][user_id]["DATA_PATH"]["value"]
        if demo and not data_path:
            study_title: str = doc_ref_dict["title"].replace(" ", "").lower()
            data_path = f"sfkit_example_data/demo/{study_title}"
        copy_results_to_cloud_storage(role, data_path, f"sfgwas/out/party{role}")

    if protocol == "SFGWAS":
        if send_results == "Yes" and doc_ref_dict["setup_configuration"] == "website":
            with open(f"sfgwas/out/party{role}/new_assoc.txt", "r") as f:
                website_send_file(f, "new_assoc.txt")

            with open(f"sfgwas/out/party{role}/manhattan.png", "rb") as f:
                website_send_file(f, "manhattan.png")

            update_firestore("update_firestore::status=Finished protocol!")
        else:
            update_firestore(
                "update_firestore::status=Finished protocol! You can view the results in your cloud storage bucket or on your machine."
            )
    elif protocol == "PCA":
        if send_results == "Yes" and doc_ref_dict["setup_configuration"] == "website":
            with open(f"sfgwas/cache/party{role}/Qpc.txt", "r") as f:
                website_send_file(f, "Qpc.txt")
            update_firestore("update_firestore::status=Finished protocol!")
        else:
            update_firestore(
                "update_firestore::status=Finished protocol! You can view the results in your cloud storage bucket or on your machine."
            )

    update_firestore(f"update_firestore::task=Running {protocol} protocol completed")


def make_new_assoc_and_manhattan_plot(doc_ref_dict: dict, demo: bool, role: str) -> None:
    # sourcery skip: assign-if-exp, introduce-default-else, swap-if-expression
    num_inds_total = 2000
    if not demo:
        num_inds_total = sum(
            int(doc_ref_dict["personal_parameters"][user]["NUM_INDS"]["value"])
            for user in doc_ref_dict["participants"]
        )
    num_covs = int(doc_ref_dict["parameters"]["num_covs"]["value"])

    snp_pos_path = f"sfgwas/example_data/party{role}/snp_pos.txt"
    if not demo:
        with open(os.path.join(constants.SFKIT_DIR, "data_path.txt"), "r") as f:
            f.readline()
            data_path = f.readline().rstrip()
            snp_pos_path = f"{data_path}/snp_pos.txt"

    postprocess_assoc(
        f"sfgwas/out/party{role}/new_assoc.txt",
        f"sfgwas/out/party{role}/assoc.txt",
        snp_pos_path,
        f"sfgwas/cache/party{role}/gkeep.txt",
        "",
        num_inds_total,
        num_covs,
    )
    plot_assoc(f"sfgwas/out/party{role}/manhattan.png", f"sfgwas/out/party{role}/new_assoc.txt")


def to_float_int_or_bool(string: str) -> Union[float, int, bool, str]:
    if string.lower() in {"true", "false"}:
        return string.lower() == "true"
    try:
        return int(string)
    except ValueError:
        try:
            return float(string)
        except ValueError:
            return string
