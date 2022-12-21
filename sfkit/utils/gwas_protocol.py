import fileinput
import multiprocessing

# import socket
import subprocess
import time

from sfkit.api import get_doc_ref_dict, update_firestore, website_send_file
from sfkit.encryption.mpc.encrypt_data import encrypt_data


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
        if subprocess.run(command, shell=True).returncode != 0:
            print(f"Failed to perform command {command}")
            exit(1)
    print("\n\n Finished installing dependencies \n\n")
    update_firestore("update_firestore::status=finished installing dependencies")


def install_gwas_repo() -> None:
    print("\n\n Begin installing GWAS repo \n\n")
    subprocess.run("git clone https://github.com/simonjmendelsohn/secure-gwas secure-gwas", shell=True)
    print("\n\n Finished installing GWAS repo \n\n")


def install_ntl_library() -> None:
    print("\n\n Begin installing NTL library \n\n")
    commands = """curl https://libntl.org/ntl-10.3.0.tar.gz --output ntl-10.3.0.tar.gz
                tar -zxvf ntl-10.3.0.tar.gz
                cp secure-gwas/code/NTL_mod/ZZ.h ntl-10.3.0/include/NTL/
                cp secure-gwas/code/NTL_mod/ZZ.cpp ntl-10.3.0/src/
                cd ntl-10.3.0/src && ./configure NTL_THREAD_BOOST=on
                cd ntl-10.3.0/src && make all
                cd ntl-10.3.0/src && sudo make install"""
    for command in commands.split("\n"):
        if subprocess.run(command, shell=True).returncode != 0:
            print(f"Failed to perform command {command}")
            exit(1)
    print("\n\n Finished installing NTL library \n\n")
    update_firestore("update_firestore::status=finished installing NTL library")


def compile_gwas_code() -> None:
    print("\n\n Begin compiling GWAS code \n\n")
    command = """cd secure-gwas/code && COMP=$(which clang++) &&\
                sed -i "s|^CPP.*$|CPP = ${COMP}|g" Makefile &&\
                sed -i "s|^INCPATHS.*$|INCPATHS = -I/usr/local/include|g" Makefile &&\
                sed -i "s|^LDPATH.*$|LDPATH = -L/usr/local/lib|g" Makefile &&\
                sudo make"""
    if subprocess.run(command, shell=True).returncode != 0:
        print(f"Failed to perform command {command}")
        exit(1)
    print("\n\n Finished compiling GWAS code \n\n")
    update_firestore("update_firestore::status=finished compiling GWAS code")


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
    if role == "0":
        command = f"mkdir -p {data_path}"
        if subprocess.run(command, shell=True).returncode != 0:
            print(f"Failed to perform command {command}")
            exit(1)
        command = f"gsutil cp gs://secure-gwas-data0/pos.txt {data_path}/pos.txt"
        if subprocess.run(command, shell=True).returncode != 0:
            print(f"Failed to perform command {command}")
            exit(1)
    elif role in {"1", "2"}:
        encrypt_data()
    update_firestore("update_firestore::status=finished encrypting data")


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
        if subprocess.run(command, shell=True).returncode != 0:
            print(f"Failed to perform command {command}")
            exit(1)
    print("\n\n Finished copying data to GWAS repo \n\n")
    update_firestore("update_firestore::status=finished copying data to GWAS repo")


def sync_with_other_vms(role: str) -> None:
    update_firestore("update_firestore::status=syncing up")
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
    update_firestore("update_firestore::status=finished syncing up")


def start_datasharing(role: str, demo: bool) -> None:
    print("\n\n Begin starting data sharing \n\n")
    update_firestore("update_firestore::status=starting data sharing protocol")
    if demo:
        command = "cd secure-gwas/code && bash run_example_datasharing.sh"
    else:
        command = f"cd secure-gwas/code && bin/DataSharingClient '{role}' ../par/test.par.'{role}'.txt"
        if role != "0":
            command += " ../test_data/"
    if subprocess.run(command, shell=True).returncode != 0:
        print(f"Failed to perform command {command}")
        exit(1)
    print("\n\n Finished starting data sharing \n\n")
    update_firestore("update_firestore::status=started data sharing protocol")


def start_gwas(role: str, demo: bool) -> None:
    print("Sleeping before starting GWAS")
    time.sleep(100 + 30 * int(role))
    print("\n\n Begin starting GWAS \n\n")
    if demo:
        command = "cd secure-gwas/code && bash run_example_gwas.sh"
    else:
        command = f"cd secure-gwas/code && bin/GwasClient '{role}' ../par/test.par.'{role}'.txt"
    if subprocess.run(command, shell=True).returncode != 0:
        print(f"Failed to perform command {command}")
        exit(1)
    print("\n\n Finished GWAS \n\n")

    if demo:
        with open("secure-gwas/out/test_assoc.txt", "r") as file:
            website_send_file(file, "assoc.txt")
        update_firestore("update_firestore::status=Finished protocol!")

    else:
        update_firestore(
            "update_firestore::status=Finished protocol!  You can view the results on your machine in the /secure-gwas/out directory"
        )
