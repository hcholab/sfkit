# TODO: update parameter files based on website
#       do the 'connect_to_other_vms' with the ports from website

import fileinput
import subprocess
import time

from sfkit.api import update_firestore
from sfkit.encryption.mpc.encrypt_data import encrypt_data


def run_gwas_protocol(doc_ref_dict: dict, role: str) -> None:
    print("\n\n Begin running GWAS protocol \n\n")
    install_gwas_dependencies()
    install_gwas_repo()
    install_ntl_library()
    compile_gwas_code()
    connect_to_other_vms(doc_ref_dict, role)
    encrypt_or_prepare_data("./encrypted_data", role)
    copy_data_to_gwas_repo("./encrypted_data", role)
    start_datasharing(role)
    start_gwas(role)


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


def connect_to_other_vms(doc_ref_dict: dict, role: str) -> None:
    print("\n\n Begin connecting to other VMs \n\n")
    ip_addresses = [
        doc_ref_dict["personal_parameters"][user]["IP_ADDRESS"]["value"] for user in doc_ref_dict["participants"]
    ]
    print("IP addresses:", ip_addresses)

    for line in fileinput.input(f"secure-gwas/par/test.par.{role}.txt", inplace=True):
        if "IP_ADDR_P0" in line:
            print(f"IP_ADDR_P0 {ip_addresses[0]}")
        elif "IP_ADDR_P1" in line:
            print(f"IP_ADDR_P1 {ip_addresses[1]}")
        elif "IP_ADDR_P2" in line:
            print(f"IP_ADDR_P2 {ip_addresses[2]}")
        else:
            print(line, end="")
    print("\n\n Finished updating parameter files \n\n")

    print("Using port 8055 to test connections")
    command = "nc -k -l -p 8055 &"
    if subprocess.run(command, shell=True).returncode != 0:
        print(f"Failed to perform command {command}")
        exit(1)
    for i in range(int(role)):
        command = f"nc -w 5 -v -z {ip_addresses[i]} 8055 &>/dev/null"
        while subprocess.run(command, shell=True).returncode != 0:
            print(f"Failed to perform command {command}. Trying again...")
            time.sleep(5)
    print("\n\n Finished connecting to other VMs \n\n")
    update_firestore("update_firestore::status=finished connecting to other VMs")


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


def start_datasharing(role: str) -> None:
    print("Sleeping before starting datasharing")
    time.sleep(30 * int(role))
    print("\n\n Begin starting data sharing \n\n")
    command = f"cd secure-gwas/code && bin/DataSharingClient '{role}' ../par/test.par.'{role}'.txt"
    if role != "0":
        command += " ../test_data/"
    if subprocess.run(command, shell=True).returncode != 0:
        print(f"Failed to perform command {command}")
        exit(1)
    print("\n\n Finished starting data sharing \n\n")
    update_firestore("update_firestore::status=started data sharing protocol")


def start_gwas(role: str) -> None:
    print("Sleeping before starting GWAS")
    time.sleep(100 + 30 * int(role))
    print("\n\n Begin starting GWAS \n\n")
    command = f"cd secure-gwas/code && bin/GwasClient '{role}' ../par/test.par.'{role}'.txt"
    if subprocess.run(command, shell=True).returncode != 0:
        print(f"Failed to perform command {command}")
        exit(1)
    print("\n\n Finished GWAS \n\n")
    update_firestore("update_firestore::status=finished protocol")

    # TODO: update both firestore and param file with number of cpus for num_threads (n_cpus=$(nproc))
    # for reference when doing the TODO to update the parameter files...
    # def update_parameters(self, file: str, study_title: str) -> None:
    #     print(f"Updating parameters in {file}")

    #     doc_ref = current_app.config["DATABASE"].collection("studies").document(study_title.replace(" ", "").lower())
    #     doc_ref_dict: dict = doc_ref.get().to_dict()

    #     pars = doc_ref_dict["parameters"]

    #     file_number = file.split(".")[-2]
    #     pars = pars | doc_ref_dict["personal_parameters"][doc_ref_dict["participants"][int(file_number)]]

    #     pars["NUM_INDS_SP_1"] = doc_ref_dict["personal_parameters"][doc_ref_dict["participants"][1]]["NUM_INDS"]
    #     pars["NUM_INDS_SP_2"] = doc_ref_dict["personal_parameters"][doc_ref_dict["participants"][2]]["NUM_INDS"]
    #     pars["NUM_INDS"] = {"value": ""}
    #     pars["NUM_INDS"]["value"] = str(int(pars["NUM_INDS_SP_1"]["value"]) + int(pars["NUM_INDS_SP_2"]["value"]))

    #     # update pars with ipaddresses
    #     for i in range(3):
    #         pars[f"IP_ADDR_P{str(i)}"] = doc_ref_dict["personal_parameters"][doc_ref_dict["participants"][i]][
    #             "IP_ADDRESS"
    #         ]
    #     # update pars with ports
    #     # pars["PORT_P0_P1"] and PORT_P0_P2 do not need to be updated as they are controlled by us (the Broad)
    #     pars["PORT_P1_P2"] = {
    #         "value": doc_ref_dict["personal_parameters"][doc_ref_dict["participants"][1]]["PORTS"]["value"].split(",")[
    #             2
    #         ]
    #     }

    #     for line in fileinput.input(file, inplace=True):
    #         key = str(line).split(" ")[0]
    #         if key in pars:
    #             line = f"{key} " + str(pars[key]["value"]) + "\n"
    #         print(line, end="")
