import os
import shutil

import tomlkit

from sfkit.api import get_doc_ref_dict, update_firestore
from sfkit.utils import constants
from sfkit.utils.helper_functions import condition_or_fail, run_command
from sfkit.utils.sfgwas_helper_functions import (
    boot_sfkit_proxy,
    get_file_paths,
    to_float_int_or_bool,
)
from sfkit.utils.sfgwas_protocol import generate_shared_keys, sync_with_other_vms


def run_sfgwas_lmm_protocol(role: str, phase: str = "", demo: bool = False) -> None:
    print("\n\n Begin running SF-GWAS-LMM protocol \n\n")
    if not demo:
        generate_shared_keys(int(role))
        print("Begin updating config files")
        update_config_local(role)
        update_config_global()
    sync_with_other_vms(role, demo)
    start_sfgwas_lmm(role, demo)


def update_config_local(role: str) -> None:
    """
    Update configLocal.Party{role}.toml for SF-GWAS-LMM
    """
    config_file_path = (
        f"{constants.EXECUTABLES_PREFIX}sfgwas-lmm/config/configLocal.Party{role}.toml"
    )

    try:
        with open(config_file_path, "r") as f:
            data = tomlkit.parse(f.read())
    except FileNotFoundError:
        print(f"File {config_file_path} not found.")
        print("Creating it...")
        shutil.copyfile(
            f"{constants.EXECUTABLES_PREFIX}sfgwas-lmm/config/configLocal.Party2.toml",
            config_file_path,
        )
        with open(config_file_path, "r") as f:
            data = tomlkit.parse(f.read())

    data["shared_keys_path"] = constants.SFKIT_DIR
    data["output_dir"] = f"out/party{role}"
    data["cache_dir"] = f"cache/party{role}"

    doc_ref_dict = get_doc_ref_dict()
    user_id: str = doc_ref_dict["participants"][int(role)]
    data["local_num_threads"] = int(
        doc_ref_dict["personal_parameters"][user_id]["NUM_CPUS"]["value"]
    )

    with open(config_file_path, "w") as f:
        f.write(tomlkit.dumps(data))


def update_config_global() -> None:
    """
    Update configGlobal.toml
    """
    print("Updating configGlobal.toml")
    doc_ref_dict: dict = get_doc_ref_dict()
    config_file_path = (
        f"{constants.EXECUTABLES_PREFIX}sfgwas-lmm/config/configGlobal.toml"
    )
    with open(config_file_path, "r") as f:
        data = tomlkit.parse(f.read())

    # Update the ip addresses and ports
    if "servers" not in data:
        data["servers"] = {}
    servers = data["servers"]
    for i, participant in enumerate(doc_ref_dict["participants"]):
        if f"party{i}" not in servers:
            servers[f"party{i}"] = {}
        party = servers[f"party{i}"]

        party["ipaddr"] = doc_ref_dict["personal_parameters"][participant][
            "IP_ADDRESS"
        ]["value"]

        ports: list = doc_ref_dict["personal_parameters"][participant]["PORTS"][
            "value"
        ].split(",")
        if "ports" not in party:
            party["ports"] = {}
        for j, port in enumerate(ports):
            if port != "null" and i != j:
                party["ports"][f"party{j}"] = port

    # if not network_only and constants.BLOCKS_MODE not in doc_ref_dict["description"]:
    data["num_main_parties"] = len(doc_ref_dict["participants"]) - 1

    row_name = "num_inds"
    col_name = "num_snps"
    data[row_name] = []
    for i, participant in enumerate(doc_ref_dict["participants"]):
        data.get(row_name, []).append(
            int(doc_ref_dict["personal_parameters"][participant]["NUM_INDS"]["value"])
        )
        print(f"{row_name} for {participant} is {data.get(row_name, [])[i]}")
        condition_or_fail(
            i == 0 or data.get(row_name, [])[i] > 0,
            f"{row_name} must be greater than 0",
        )
    data[col_name] = int(doc_ref_dict["parameters"]["num_snps"]["value"])
    print(f"{col_name} is {data[col_name]}")
    condition_or_fail(data.get(col_name, 0) > 0, f"{col_name} must be greater than 0")

    # shared and advanced parameters
    pars = {**doc_ref_dict["parameters"], **doc_ref_dict["advanced_parameters"]}
    for key, value in pars.items():
        if key in data:
            data[key] = to_float_int_or_bool(value["value"])

    with open(config_file_path, "w") as f:
        f.write(tomlkit.dumps(data))


def start_sfgwas_lmm(role: str, demo: bool) -> None:
    update_firestore("update_firestore::task=Performing SF-GWAS-LMM protocol")
    print("\n\n starting SF-GWAS-LMM \n\n")

    cwd = os.getcwd()
    sfkit_proxy = None

    if constants.SFKIT_PROXY_ON:
        sfkit_proxy = boot_sfkit_proxy(
            role,
            f"{constants.EXECUTABLES_PREFIX}sfgwas-lmm/config/configGlobal.toml",
        )

    os.chdir(f"{constants.EXECUTABLES_PREFIX}sfgwas-lmm/scripts")

    if int(role) > 0:
        _, data_path = get_file_paths()
        run_command(
            ["data_prep.sh", role, data_path],
            fail_message="Failed data prep",
        )

    sync_with_other_vms(role, demo)

    env = os.environ.copy()
    env["PID"] = role

    # PID=$2 sfgwas-lmm -test.run "$1" -test.timeout 96h
    for test in ["TestLevel0", "TestLevel1", "TestAssoc"]:
        update_firestore(f"update_firestore::task={test}")
        run_command(
            ["sfgwas-lmm", "-test.run", test, "-test.timeout", "96h"],
            fail_message=f"Failed SF-GWAS-LMM {test}",
            role=role,
        )
        sync_with_other_vms(role, demo)

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

    _send_results: str = (
        doc_ref_dict["personal_parameters"][user_id]
        .get("SEND_RESULTS", {})
        .get("value")
    )

    # if send_results == "Yes":
    #     output_dir = f"{constants.EXECUTABLES_PREFIX}sfgwas-lmm/out/party{role}"

    #     assoc_file = os.path.join(output_dir, "assoc_results.txt")
    #     if os.path.exists(assoc_file):
    #         with open(assoc_file, "rb") as f:
    #             website_send_file(f, "assoc_results.txt")
