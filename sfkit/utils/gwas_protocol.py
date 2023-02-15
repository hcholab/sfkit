import fileinput
import multiprocessing
import time

from sfkit.api import get_doc_ref_dict, update_firestore, website_send_file
from sfkit.encryption.mpc.encrypt_data import encrypt_data
from sfkit.utils.helper_functions import (
    condition_or_fail,
    copy_results_to_cloud_storage,
    plot_assoc,
    postprocess_assoc,
    run_command,
)


def run_gwas_protocol(role: str, demo: bool = False) -> None:
    print("\n\n Begin running GWAS protocol \n\n")
    install_gwas_dependencies()
    install_gwas_repo()
    install_ntl_library()
    compile_gwas_code()
    if not demo:
        update_parameters(role)
        # connect_to_other_vms(role)
        encrypt_or_prepare_data("./encrypted_data", role)
        copy_data_to_gwas_repo("./encrypted_data", role)
        sync_with_other_vms(role)
    start_datasharing(role, demo)
    start_gwas(role, demo)


def install_gwas_dependencies() -> None:
    update_firestore("update_firestore::task=Installing dependencies")
    print("\n\n Begin installing dependencies \n\n")
    commands = """sudo apt-get --assume-yes update 
                    sudo apt-get --assume-yes install build-essential 
                    sudo apt-get --assume-yes install clang-3.9 
                    sudo apt-get --assume-yes install libgmp3-dev 
                    sudo apt-get --assume-yes install libssl-dev 
                    sudo apt-get --assume-yes install libsodium-dev 
                    sudo apt-get --assume-yes install libomp-dev 
                    sudo apt-get --assume-yes install netcat 
                    sudo apt-get --assume-yes install git 
                    sudo apt-get --assume-yes install python3-pip 
                    sudo pip3 install numpy"""
    for command in commands.split("\n"):
        run_command(command)
    print("\n\n Finished installing dependencies \n\n")
    update_firestore("update_firestore::task=Installing dependencies completed")


def install_gwas_repo() -> None:
    print("\n\n Begin installing GWAS repo \n\n")
    command = "git clone https://github.com/simonjmendelsohn/secure-gwas secure-gwas"
    run_command(command)
    print("\n\n Finished installing GWAS repo \n\n")


def install_ntl_library() -> None:
    update_firestore("update_firestore::task=Installing NTL library")
    print("\n\n Begin installing NTL library \n\n")
    commands = """curl https://libntl.org/ntl-10.3.0.tar.gz --output ntl-10.3.0.tar.gz
                tar -zxvf ntl-10.3.0.tar.gz
                cp secure-gwas/code/NTL_mod/ZZ.h ntl-10.3.0/include/NTL/
                cp secure-gwas/code/NTL_mod/ZZ.cpp ntl-10.3.0/src/
                cd ntl-10.3.0/src && ./configure NTL_THREAD_BOOST=on
                cd ntl-10.3.0/src && make all
                cd ntl-10.3.0/src && sudo make install"""
    for command in commands.split("\n"):
        run_command(command)
    print("\n\n Finished installing NTL library \n\n")
    update_firestore("update_firestore::task=Installing NTL library completed")


def compile_gwas_code() -> None:
    update_firestore("update_firestore::task=Compiling GWAS code")
    print("\n\n Begin compiling GWAS code \n\n")
    command = """cd secure-gwas/code && COMP=$(which clang++) &&\
                sed -i "s|^CPP.*$|CPP = ${COMP}|g" Makefile &&\
                sed -i "s|^INCPATHS.*$|INCPATHS = -I/usr/local/include|g" Makefile &&\
                sed -i "s|^LDPATH.*$|LDPATH = -L/usr/local/lib|g" Makefile &&\
                sudo make"""
    run_command(command)
    print("\n\n Finished compiling GWAS code \n\n")
    update_firestore("update_firestore::task=Compiling GWAS code completed")


def update_parameters(role: str) -> None:
    print(f"\n\n Updating parameters in 'secure-gwas/par/test.par.{role}.txt'\n\n")

    doc_ref_dict = get_doc_ref_dict()

    # shared parameters and advanced parameters
    pars = doc_ref_dict["parameters"] | doc_ref_dict["advanced_parameters"]

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
        pars[f"IP_ADDR_P{i}"] = {"value": ip}

        ports = doc_ref_dict["personal_parameters"][doc_ref_dict["participants"][i]]["PORTS"]["value"]
        for j in range(i + 1, 3):
            pars[f"PORT_P{i}_P{j}"] = {"value": ports.split(",")[j]}

    for line in fileinput.input(f"secure-gwas/par/test.par.{role}.txt", inplace=True):
        key = str(line).split(" ")[0]
        if key in pars:
            line = f"{key} " + str(pars[key]["value"]) + "\n"
        print(line, end="")


# this function currently has 2 main problems: 1. the other machine doesn't receive the connection 2. it uses the same ports as the main protocol, causing a conflict
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


def encrypt_or_prepare_data(data_path: str, role: str) -> None:
    update_firestore("update_firestore::task=Encrypting data")
    doc_ref_dict: dict = get_doc_ref_dict()
    study_title: str = doc_ref_dict["title"].replace(" ", "").lower()

    if role == "0":
        command = f"mkdir -p {data_path}"
        run_command(command)
        command = f"gsutil cp gs://sfkit/{study_title}/pos.txt {data_path}/pos.txt"
        run_command(command)
    elif role in {"1", "2"}:
        try:
            encrypt_data()
        except Exception as e:
            condition_or_fail(False, f"encrypt_data::error={e}")
    update_firestore("update_firestore::task=Encrypting data completed")


def copy_data_to_gwas_repo(data_path: str, role: str) -> None:
    print("\n\n Copy data to GWAS repo \n\n")
    commands = f"""cp '{data_path}'/g.bin secure-gwas/test_data/g.bin 
    cp '{data_path}'/m.bin secure-gwas/test_data/m.bin 
    cp '{data_path}'/p.bin secure-gwas/test_data/p.bin 
    cp '{data_path}'/other_shared_key.bin secure-gwas/test_data/other_shared_key.bin 
    cp '{data_path}'/pos.txt secure-gwas/test_data/pos.txt"""

    if role == "0":
        # assuming CP0's pos.txt is in ./encrypted folder
        commands = f"cp '{data_path}'/pos.txt secure-gwas/test_data/pos.txt"

    for command in commands.split("\n"):
        run_command(command)
    print("\n\n Finished copying data to GWAS repo \n\n")


def sync_with_other_vms(role: str) -> None:
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
    update_firestore("update_firestore::task=Syncing up machines completed")


def start_datasharing(role: str, demo: bool) -> None:
    update_firestore("update_firestore::task=Performing data sharing protocol")
    print("\n\n starting data sharing protocol \n\n")
    if demo:
        command = "cd secure-gwas/code && bash run_example_datasharing.sh"
    else:
        command = f"cd secure-gwas/code && bin/DataSharingClient '{role}' ../par/test.par.'{role}'.txt"
        if role != "0":
            command += " ../test_data/"
    run_command(command, fail_message="Failed MPC-GWAS data sharing protocol")
    print("\n\n Finished data sharing protocol\n\n")
    update_firestore("update_firestore::task=Performing data sharing protocol completed")


def start_gwas(role: str, demo: bool) -> None:
    update_firestore("update_firestore::task=Performing GWAS protocol")
    print("Sleeping before starting GWAS")
    time.sleep(100 + 30 * int(role))
    print("\n\n starting GWAS \n\n")
    update_firestore("update_firestore::status=starting GWAS")
    if demo:
        command = "cd secure-gwas/code && bash run_example_gwas.sh"
    else:
        command = f"cd secure-gwas/code && bin/GwasClient '{role}' ../par/test.par.'{role}'.txt"
    run_command(command, fail_message="Failed MPC-GWAS protocol")
    print("\n\n Finished GWAS \n\n")

    if role != "0":
        process_output_files(role, demo)
    else:
        update_firestore("update_firestore::status=Finished protocol!")
    update_firestore("update_firestore::task=Performing GWAS protocol completed")


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
        "secure-gwas/out/new_assoc.txt",
        "secure-gwas/out/test_assoc.txt",
        "secure-gwas/test_data/pos.txt",
        "secure-gwas/out/test_gkeep1.txt",
        "secure-gwas/out/test_gkeep2.txt",
        num_inds_total,
        num_covs,
    )
    plot_assoc("secure-gwas/out/manhattan.png", "secure-gwas/out/new_assoc.txt")

    doc_ref_dict: dict = get_doc_ref_dict()
    user_id: str = doc_ref_dict["participants"][int(role)]
    send_results: str = doc_ref_dict["personal_parameters"][user_id].get("SEND_RESULTS", {}).get("value")

    # copy results to cloud storage
    if doc_ref_dict["setup_configuration"] == "website":
        data_path = doc_ref_dict["personal_parameters"][user_id]["DATA_PATH"]["value"]
        if demo and not data_path:
            study_title: str = doc_ref_dict["title"].replace(" ", "").lower()
            data_path = f"sfkit_example_data/demo/{study_title}"
        copy_results_to_cloud_storage(role, data_path, "secure-gwas/out")

    if send_results == "Yes" and doc_ref_dict["setup_configuration"] == "website":
        with open("secure-gwas/out/new_assoc.txt", "r") as file:
            website_send_file(file, "new_assoc.txt")

        with open("secure-gwas/out/manhattan.png", "rb") as file:
            website_send_file(file, "manhattan.png")

        update_firestore("update_firestore::status=Finished protocol!")
    else:
        update_firestore(
            "update_firestore::status=Finished protocol! You can view the results in your cloud storage bucket or on your machine."
        )
