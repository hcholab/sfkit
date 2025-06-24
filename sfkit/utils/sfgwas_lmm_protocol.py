import fileinput
import os
import shutil
import time

import tomlkit

from sfkit.api import get_doc_ref_dict, update_firestore
from sfkit.utils import constants
from sfkit.utils.helper_functions import run_command
from sfkit.utils.sfgwas_helper_functions import (boot_sfkit_proxy,
                                                 get_file_paths)
from sfkit.utils.sfgwas_protocol import update_config_global


def run_sfgwas_lmm_protocol(role: str, phase: str = "", demo: bool = False) -> None:
    print("\n\n Begin running SF-GWAS-LMM protocol \n\n")
    if not demo:
        update_parameters(role)
        sync_with_other_vms(role)
        update_config_global(protocol="sfgwas-lmm", network_only=True)
    update_config_local(role)
    update_config_global_phase(phase, demo)
    start_sfgwas_lmm(role, demo)


def update_parameters(role: str) -> None:
    print(f"\n\n Updating parameters for party {role}\n\n")

    import multiprocessing
    num_cpus = str(multiprocessing.cpu_count())
    update_firestore(f"update_firestore::NUM_THREADS={num_cpus}")
    update_firestore(f"update_firestore::NUM_CPUS={num_cpus}")


def update_config_local(role: str) -> None:
    """
    Update configLocal.Party{role}.toml for SF-GWAS-LMM
    """
    config_file_path = f"{constants.EXECUTABLES_PREFIX}sfgwas-lmm/config/configLocal.Party{role}.toml"

    try:
        with open(config_file_path, "r") as f:
            data = tomlkit.parse(f.read())
    except FileNotFoundError:
        print(f"File {config_file_path} not found.")
        print("Creating it...")
        shutil.copyfile(
            f"{constants.EXECUTABLES_PREFIX}sfgwas-lmm/config/configLocal.Party2.toml",
            config_file_path
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
    data["mpc_num_threads"] = int(doc_ref_dict["personal_parameters"][user_id]["NUM_CPUS"]["value"])
    data["memory_limit"] = int(int(data.get("mpc_num_threads", 16)) * 8 * 1_000_000_000)

    with open(config_file_path, "w") as f:
        f.write(tomlkit.dumps(data))


def update_data_file_paths(data: dict) -> None:
    """
    Update data file paths in config for SF-GWAS-LMM
    """
    geno_file_prefix, data_path = get_file_paths()

    data["geno_binary_file_prefix"] = f"{geno_file_prefix}"
    data["pheno_file"] = f"{data_path}/pheno.txt"
    data["covar_file"] = f"{data_path}/cov.txt"
    data["snp_position_file"] = f"{data_path}/snp_pos.txt"
    data["sample_keep_file"] = f"{data_path}/sample_keep.txt"
    data["snp_ids_file"] = f"{data_path}/snp_ids.txt"
    data["geno_count_file"] = f"{data_path}/geno/all.gcount.transpose.bin"
    data["chrom_sizes_file"] = f"{data_path}/chrom_sizes.txt"

    data["block_sizes_file"] = f"{data_path}/blockSizes.txt"
    data["block_to_chrom_file"] = f"{data_path}/blockToChrom.txt"
    data["fold_sizes_file"] = f"{data_path}/foldSizes.txt"


def update_config_global_phase(phase: str, demo: bool) -> None:
    """
    Update phase-specific settings in configGlobal.toml
    """
    config_file_path = f"{constants.EXECUTABLES_PREFIX}sfgwas-lmm/config/configGlobal.toml"
    with open(config_file_path, "r") as f:
        data = tomlkit.parse(f.read())

    if demo:
        data["mpc_num_threads"] = 6
        data["mpc_num_main_threads"] = 1
        data["num_snps"] = 1000
        data["step_2_num_snps"] = 1000

    with open(config_file_path, "w") as f:
        f.write(tomlkit.dumps(data))


def sync_with_other_vms(role: str) -> None:
    update_firestore("update_firestore::status=syncing up")
    update_firestore("update_firestore::task=Syncing up machines")
    print("Begin syncing up")

    # Wait until all participants have the status of syncing up
    while True:
        doc_ref_dict: dict = get_doc_ref_dict()
        statuses = doc_ref_dict["status"].values()
        if all(status == "syncing up" for status in statuses):
            break
        print("Waiting for all participants to sync up...")
        time.sleep(5)
    print("Finished syncing up")


def start_sfgwas_lmm(role: str, demo: bool) -> None:
    update_firestore("update_firestore::task=Performing SF-GWAS-LMM protocol")
    print("\n\n Starting SF-GWAS-LMM \n\n")

    cwd = os.getcwd()
    command = []
    sfkit_proxy = None

    if constants.SFKIT_PROXY_ON:
        sfkit_proxy = boot_sfkit_proxy(role=role)

        proxychains_conf = os.path.join(cwd, "proxychains.conf")
        shutil.copy2("/etc/proxychains.conf", proxychains_conf)
        for line in fileinput.input(proxychains_conf, inplace=True):
            if line.startswith("socks"):
                line = f"socks5 127.0.0.1 {constants.SFKIT_PROXY_PORT}\n"
            print(line, end="")
        command += ["proxychains", "-f", proxychains_conf]

    os.chdir(f"{constants.EXECUTABLES_PREFIX}sfgwas-lmm/scripts")
    command += ["sfgwas-lmm"]

    env = os.environ.copy()
    env["PID"] = role

    run_command(
        command,
        fail_message="Failed SF-GWAS-LMM protocol"
    )

    os.chdir(cwd)

    if sfkit_proxy:
        sfkit_proxy.terminate()

    print("\n\n Finished SF-GWAS-LMM \n\n")

    if int(role):
        process_output_files(role)

    update_firestore("update_firestore::status=Finished protocol!")


def process_output_files(role: str) -> None:
    """
    Process and send results from SF-GWAS-LMM
    """
    doc_ref_dict: dict = get_doc_ref_dict()
    user_id: str = doc_ref_dict["participants"][int(role)]

    send_results: str = (
        doc_ref_dict["personal_parameters"][user_id]
        .get("SEND_RESULTS", {})
        .get("value")
    )

    if send_results == "Yes":
        from sfkit.api import website_send_file

        output_dir = f"{constants.EXECUTABLES_PREFIX}sfgwas-lmm/out/party{role}"

        assoc_file = os.path.join(output_dir, "assoc_results.txt")
        if os.path.exists(assoc_file):
            with open(assoc_file, "rb") as f:
                website_send_file(f, "assoc_results.txt")