import fileinput
import multiprocessing
import os
import shutil
import time
from shutil import copy2

from google.cloud import storage

from sfkit.api import get_doc_ref_dict, update_firestore, website_send_file
from sfkit.utils import constants
from sfkit.utils.helper_functions import (
    copy_results_to_cloud_storage,
    copy_to_out_folder,
    plot_assoc,
    postprocess_assoc,
    run_command,
)


def run_gwas_protocol(role: str, demo: bool = False) -> None:
    print("\n\n Begin running GWAS protocol \n\n")
    if not (constants.IS_DOCKER or constants.IS_INSTALLED_VIA_SCRIPT):
        install_gwas_dependencies()
        install_gwas_repo()
        install_ntl_library()
        compile_gwas_code()
    if not demo:
        update_parameters(role)
        # connect_to_other_vms(role)
        prepare_data(constants.ENCRYPTED_DATA_FOLDER, role)
        copy_data_to_gwas_repo(constants.ENCRYPTED_DATA_FOLDER, role)
        sync_with_other_vms(role)
    start_datasharing(role, demo)
    start_gwas(role, demo)


def install_gwas_dependencies() -> None:
    update_firestore("update_firestore::task=Installing dependencies")
    print("\n\n Begin installing dependencies \n\n")
    commands = [
        ["sudo", "apt-get", "--assume-yes", "update"],
        ["sudo", "apt-get", "--assume-yes", "install", "build-essential"],
        ["sudo", "apt-get", "--assume-yes", "install", "clang-3.9"],
        ["sudo", "apt-get", "--assume-yes", "install", "libgmp3-dev"],
        ["sudo", "apt-get", "--assume-yes", "install", "libssl-dev"],
        ["sudo", "apt-get", "--assume-yes", "install", "libsodium-dev"],
        ["sudo", "apt-get", "--assume-yes", "install", "libomp-dev"],
        ["sudo", "apt-get", "--assume-yes", "install", "netcat-openbsd"],
        ["sudo", "apt-get", "--assume-yes", "install", "git"],
        ["sudo", "apt-get", "--assume-yes", "install", "python3-pip"],
        ["pip3", "install", "numpy"],
    ]
    for command in commands:
        run_command(command)
    print("\n\n Finished installing dependencies \n\n")


def install_gwas_repo() -> None:
    update_firestore("update_firestore::task=Installing GWAS repo")
    print("\n\n Begin installing GWAS repo \n\n")
    if os.path.exists("secure-gwas"):
        shutil.rmtree("secure-gwas")
    run_command(["git", "clone", "https://github.com/hcholab/secure-gwas", "secure-gwas"])
    print("\n\n Finished installing GWAS repo \n\n")


def install_ntl_library() -> None:
    update_firestore("update_firestore::task=Installing NTL library")
    print("\n\n Begin installing NTL library \n\n")
    commands = [
        ["curl", "https://libntl.org/ntl-10.3.0.tar.gz", "--output", "ntl-10.3.0.tar.gz"],
        ["tar", "-zxvf", "ntl-10.3.0.tar.gz"],
        ["cp", "secure-gwas/code/NTL_mod/ZZ.h", "ntl-10.3.0/include/NTL/"],
        ["cp", "secure-gwas/code/NTL_mod/ZZ.cpp", "ntl-10.3.0/src/"],
    ]
    for command in commands:
        run_command(command)

    os.chdir("ntl-10.3.0/src")
    configure_commands = [["./configure", "NTL_THREAD_BOOST=on"], ["make", "all"], ["sudo", "make", "install"]]
    for command in configure_commands:
        run_command(command)
    os.chdir("../..")

    print("\n\n Finished installing NTL library \n\n")


def compile_gwas_code() -> None:
    update_firestore("update_firestore::task=Compiling GWAS code")
    print("\n\n Begin compiling GWAS code \n\n")
    os.chdir("secure-gwas/code")
    comp = shutil.which("clang++")
    if comp is None:
        raise FileNotFoundError("clang++ compiler not found.")

    makefile_path = "Makefile"
    with open(makefile_path, "r") as file:
        lines = file.readlines()

    with open(makefile_path, "w") as file:
        for line in lines:
            if line.startswith("CPP ="):
                file.write(f"CPP = {comp}\n")
            elif line.startswith("INCPATHS ="):
                file.write("INCPATHS = -I/usr/local/include\n")
            elif line.startswith("LDPATH ="):
                file.write("LDPATH = -L/usr/local/lib\n")
            else:
                file.write(line)

    run_command(["sudo", "make"])
    os.chdir("../..")

    print("\n\n Finished compiling GWAS code \n\n")


def update_parameters(role: str) -> None:
    print(f"\n\n Updating parameters in 'secure-gwas/par/test.par.{role}.txt'\n\n")

    doc_ref_dict = get_doc_ref_dict()

    # shared parameters and advanced parameters
    pars = {**doc_ref_dict["parameters"], **doc_ref_dict["advanced_parameters"]}

    # individual parameters
    for i in range(1, len(doc_ref_dict["participants"])):
        pars[f"NUM_INDS_SP_{i}"] = doc_ref_dict["personal_parameters"][doc_ref_dict["participants"][i]]["NUM_INDS"]

    pars["NUM_INDS"] = {"value": ""}
    pars["NUM_INDS"]["value"] = str(int(pars["NUM_INDS_SP_1"]["value"]) + int(pars["NUM_INDS_SP_2"]["value"]))

    # num threads = num_cpus = $(nproc)
    num_cpus = str(multiprocessing.cpu_count())
    pars["NUM_THREADS"] = {"value": num_cpus}
    update_firestore(f"update_firestore::NUM_THREADS={num_cpus}")
    update_firestore(f"update_firestore::NUM_CPUS={num_cpus}")

    # update pars with ipaddresses and ports
    for i in range(len(doc_ref_dict["participants"])):
        ip = doc_ref_dict["personal_parameters"][doc_ref_dict["participants"][i]]["IP_ADDRESS"]["value"]
        while ip == "":
            print(f"IP address for {doc_ref_dict['participants'][i]} is empty. Waiting...")
            time.sleep(5)

            doc_ref_dict = get_doc_ref_dict()
            ip = doc_ref_dict["personal_parameters"][doc_ref_dict["participants"][i]]["IP_ADDRESS"]["value"]

        pars[f"IP_ADDR_P{i}"] = {"value": ip}

        ports = doc_ref_dict["personal_parameters"][doc_ref_dict["participants"][i]]["PORTS"]["value"]
        for j in range(i + 1, 3):
            pars[f"PORT_P{i}_P{j}"] = {"value": ports.split(",")[j]}

    for line in fileinput.input(f"{constants.EXECUTABLES_PREFIX}secure-gwas/par/test.par.{role}.txt", inplace=True):
        key = str(line).split(" ")[0]
        if key in pars:
            line = f"{key} " + str(pars[key]["value"]) + "\n"
        print(line, end="")


# this function currently has 2 main problems: 1. the other machine doesn't consistently receive the connection 2. it uses the same ports as the main protocol, causing a conflict
# def connect_to_other_vms(role: str) -> None:
#     print("\n\n Begin connecting to other VMs \n\n")

#     doc_ref_dict: dict = get_doc_ref_dict()

#     for i in range(int(role)):
#         other_user = doc_ref_dict["participants"][i]
#         ip_address = doc_ref_dict["personal_parameters"][other_user]["IP_ADDRESS"]["value"]
#         port = int(doc_ref_dict["personal_parameters"][other_user]["PORTS"]["value"].split(",")[int(role)])

#         while ip_address == "" or port == "":
#             print(f"Waiting for {other_user} to finish setting up...")
#             time.sleep(5)
#             doc_ref_dict = get_doc_ref_dict()
#             ip_address = doc_ref_dict["personal_parameters"][other_user]["IP_ADDRESS"]["value"]
#             port = int(doc_ref_dict["personal_parameters"][other_user]["PORTS"]["value"].split(",")[int(role)])

#         print(f"Connecting to {other_user} at {ip_address}:{port}...")

#         while True:
#             try:
#                 sock = socket.create_connection((ip_address, port), timeout=5)
#                 sock.close()
#                 break
#             except socket.timeout:
#                 print(f"Timed out while connecting to {other_user} at {ip_address}:{port}. Trying again...")
#             except socket.error:
#                 print(f"Error while connecting to {other_user} at {ip_address}:{port}. Trying again...")
#                 time.sleep(5)
#     print("\n\n Finished connecting to other VMs \n\n")


def prepare_data(data_path: str, role: str) -> None:
    doc_ref_dict: dict = get_doc_ref_dict()
    study_title: str = doc_ref_dict["title"]

    if role == "0":
        os.makedirs(data_path, exist_ok=True)
        storage.Client().bucket("sfkit").blob(f"{study_title}/pos.txt").download_to_filename(f"{data_path}/pos.txt")


def copy_data_to_gwas_repo(
    data_path: str, role: str
) -> None:  # TODO: change the path in parameter file instead? Or move instead of copy?
    print("\n\n Copy data to GWAS repo \n\n")
    files_to_copy = ["g.bin", "m.bin", "p.bin", "other_shared_key.bin", "pos.txt"] if role != "0" else ["pos.txt"]
    for file_name in files_to_copy:
        src_file_path = os.path.join(data_path, file_name)
        dest_file_path = os.path.join("secure-gwas/test_data", file_name)
        copy2(src_file_path, dest_file_path)
    print("\n\n Finished copying data to GWAS repo \n\n")


def sync_with_other_vms(role: str) -> None:
    update_firestore("update_firestore::status=syncing up")
    update_firestore("update_firestore::task=Syncing up machines")
    print("Begin syncing up")
    # wait until all participants have the status of starting data sharing protocol
    while True:
        doc_ref_dict: dict = get_doc_ref_dict()
        statuses = doc_ref_dict["status"].values()
        if all(status == "syncing up" for status in statuses):
            break
        print("Waiting for all participants to sync up...")
        time.sleep(5)
    time.sleep(15 + 15 * int(role))
    print("Finished syncing up")


def start_datasharing(role: str, demo: bool) -> None:
    update_firestore("update_firestore::task=Performing data sharing protocol")
    print("\n\n starting data sharing protocol \n\n")

    os.chdir(f"{constants.EXECUTABLES_PREFIX}secure-gwas/code")
    if demo:
        command = ["bash", "run_example_datasharing.sh"]
    else:
        command = ["bin/DataSharingClient", role, f"../par/test.par.{role}.txt"]
        if role != "0":
            command.append("../test_data/")
    run_command(command, fail_message="Failed MPC-GWAS data sharing protocol")

    print("\n\n Finished data sharing protocol\n\n")


def start_gwas(role: str, demo: bool) -> None:
    update_firestore("update_firestore::task=Performing GWAS protocol")
    print("Sleeping before starting GWAS")
    time.sleep(100 + 30 * int(role))
    print("\n\n starting GWAS \n\n")
    update_firestore("update_firestore::status=starting GWAS")

    os.chdir(f"{constants.EXECUTABLES_PREFIX}secure-gwas/code")
    if demo:
        command = ["bash", "run_example_gwas.sh"]
    else:
        command = ["bin/GwasClient", role, f"../par/test.par.{role}.txt"]
    run_command(command, fail_message="Failed MPC-GWAS protocol")

    print("\n\n Finished GWAS \n\n")

    if role != "0":
        process_output_files(role, demo)

    update_firestore("update_firestore::status=Finished protocol!")


def process_output_files(role: str, demo: bool) -> None:
    # sourcery skip: assign-if-exp, introduce-default-else, swap-if-expression
    doc_ref_dict = get_doc_ref_dict()
    num_inds_total = 1_000
    if not demo:
        num_inds_total = sum(
            int(doc_ref_dict["personal_parameters"][user]["NUM_INDS"]["value"])
            for user in doc_ref_dict["participants"]
        )
    num_covs = int(doc_ref_dict["parameters"]["NUM_COVS"]["value"])

    postprocess_assoc(
        f"{constants.EXECUTABLES_PREFIX}secure-gwas/out/new_assoc.txt",
        f"{constants.EXECUTABLES_PREFIX}secure-gwas/out/test_assoc.txt",
        f"{constants.EXECUTABLES_PREFIX}secure-gwas/test_data/pos.txt",
        f"{constants.EXECUTABLES_PREFIX}secure-gwas/out/test_gkeep1.txt",
        f"{constants.EXECUTABLES_PREFIX}secure-gwas/out/test_gkeep2.txt",
        num_inds_total,
        num_covs,
    )
    plot_assoc(
        f"{constants.EXECUTABLES_PREFIX}secure-gwas/out/manhattan.png",
        f"{constants.EXECUTABLES_PREFIX}secure-gwas/out/new_assoc.txt",
    )

    doc_ref_dict: dict = get_doc_ref_dict()
    user_id: str = doc_ref_dict["participants"][int(role)]

    relevant_paths = [f"{constants.EXECUTABLES_PREFIX}secure-gwas/out"]
    copy_to_out_folder(relevant_paths)

    if results_path := doc_ref_dict["personal_parameters"][user_id].get("RESULTS_PATH", {}).get("value", ""):
        copy_results_to_cloud_storage(role, results_path, f"{constants.EXECUTABLES_PREFIX}secure-gwas/out")

    send_results: str = doc_ref_dict["personal_parameters"][user_id].get("SEND_RESULTS", {}).get("value")
    if send_results == "Yes":
        with open(f"{constants.EXECUTABLES_PREFIX}secure-gwas/out/new_assoc.txt", "r") as file:
            website_send_file(file, "new_assoc.txt")

        with open(f"{constants.EXECUTABLES_PREFIX}secure-gwas/out/manhattan.png", "rb") as file:
            website_send_file(file, "manhattan.png")
