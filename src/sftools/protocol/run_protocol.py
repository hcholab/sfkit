import os
import subprocess
import time

from google.cloud import firestore
from sftools.protocol.utils import constants
from sftools.protocol.utils.google_cloud_pubsub import GoogleCloudPubsub


def run_protocol() -> None:
    with open(constants.AUTH_FILE, "r") as f:
        email = f.readline().rstrip()
        study_title = f.readline().rstrip()
        sa_key_file = f.readline().rstrip()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = sa_key_file

    doc_ref = firestore.Client().collection("studies").document(study_title.replace(" ", "").lower())
    doc_ref_dict: dict = doc_ref.get().to_dict()  # type: ignore
    role: str = str(doc_ref_dict["participants"].index(email))
    statuses: dict = doc_ref_dict["status"]

    if statuses[email] in ["['']", "['validating']", "['invalid data']"]:
        print("You have not successfully validated your data.  Please do so before proceeding.")
        return

    gcloudPubsub = GoogleCloudPubsub(constants.SERVER_GCP_PROJECT, role, study_title)
    if statuses[email] == ["not ready"]:
        statuses[email] = ["ready"]
        gcloudPubsub.publish(f"update_firestore::status=ready::{study_title}::{email}")

    while any(s in str(statuses.values()) for s in ["['']", "['validating']", "['invalid data']", "['not ready']"]):
        print("The other participant is not yet ready.  Waiting... (press CTRL-C to cancel)")
        time.sleep(5)
        statuses = doc_ref.get().to_dict()["status"]

    if statuses[email] == ["ready"]:
        gcloudPubsub.publish(f"update_firestore::status=running::{study_title}::{email}")

        if role == "1":
            print("Asking cp0 to set up their part as well...")
            time.sleep(1)
            gcloudPubsub.publish(f"run_protocol_for_cp0::{study_title}")

        install_dependencies()
        install_gwas_repo()
        install_ntl_library()
        compile_gwas_code()
        connect_to_other_vms(role, doc_ref)
        copy_data_to_gwas_repo("./encrypted_data", role)
        start_datasharing(role)
        start_gwas(role)
    else:
        print("You status is not ready.  Exiting now.")
        return


def install_gwas_repo():
    print("\n\n Begin installing GWAS repo \n\n")
    subprocess.run("git clone https://github.com/simonjmendelsohn/secure-gwas secure-gwas", shell=True)
    print("\n\n Finished installing GWAS repo \n\n")


def install_dependencies():
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


def install_ntl_library():
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


def copy_data_to_gwas_repo(data_path, role):
    print("\n\n Copy data to GWAS repo \n\n")
    commands = f"""cp '{data_path}'/g.bin secure-gwas/test_data/g.bin 
    cp '{data_path}'/m.bin secure-gwas/test_data/m.bin 
    cp '{data_path}'/p.bin secure-gwas/test_data/p.bin 
    cp '{data_path}'/other_shared_key.bin secure-gwas/test_data/other_shared_key.bin 
    cp '{data_path}'/pos.txt secure-gwas/test_data/pos.txt 
    gsutil cp gs://secure-gwas-data/test.par.'{role}'.txt secure-gwas/par/test.par.'{role}'.txt"""
    for command in commands.split("\n"):
        if subprocess.run(command, shell=True).returncode != 0:
            print(f"Failed to perform command {command}")
            exit(1)
    print("\n\n Finished copying data to GWAS repo \n\n")


def compile_gwas_code():
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


def connect_to_other_vms(role: str, doc_ref):
    doc_ref_dict = doc_ref.get().to_dict()
    print("\n\n Begin connecting to other VMs \n\n")
    ip_addresses = [
        doc_ref_dict["personal_parameters"][user]["IP_ADDRESS"]["value"] for user in doc_ref_dict["participants"]
    ]
    print("IP addresses:", ip_addresses)
    ports = [
        doc_ref_dict["personal_parameters"][user]["PORTS"]["value"].split(",") for user in doc_ref_dict["participants"]
    ]
    # print("Ports:", ports)
    print("Using port 8055 for testing")
    if role == "1":
        # command = f"nc -k -l -p '{ports[1][2]}' &"
        command = "nc -k -l -p 8055 &"
        if subprocess.run(command, shell=True).returncode != 0:
            print(f"Failed to perform command {command}")
            exit(1)
        # command = f"nc -w 5 -v -z '{ip_addresses[0]}' '{ports[0][1]}'"
        command = f"nc -w 5 -v -z '{ip_addresses[0]}' '8055'"
        while subprocess.run(command, shell=True).returncode != 0:
            time.sleep(5)
    elif role == "2":
        # command = f"nc -w 5 -v -z '{ip_addresses[0]}' '{ports[0][2]}'"
        command = f"nc -w 5 -v -z '{ip_addresses[0]}' '8055'"
        while subprocess.run(command, shell=True).returncode != 0:
            time.sleep(5)
        # command = f"nc -w 5 -v -z '{ip_addresses[1]}' '{ports[1][2]}'"
        command = f"nc -w 5 -v -z '{ip_addresses[0]}' '8055'"
        while subprocess.run(command, shell=True).returncode != 0:
            time.sleep(5)
    else:
        raise ValueError("Invalid role")
    print("\n\n Finished connecting to other VMs \n\n")


def start_datasharing(role):
    print("Sleeping before starting datasharing")
    time.sleep(30 * int(role))
    print("\n\n Begin starting data sharing \n\n")
    command = f"cd secure-gwas/code && bin/DataSharingClient '{role}' ../par/test.par.'{role}'.txt ../test_data/"
    if subprocess.run(command, shell=True).returncode != 0:
        print(f"Failed to perform command {command}")
        exit(1)
    print("\n\n Finished starting data sharing \n\n")


def start_gwas(role):
    print("Sleeping before starting GWAS")
    time.sleep(100 + 30 * int(role))
    print("\n\n Begin starting GWAS \n\n")
    command = f"cd secure-gwas/code && bin/GwasClient '{role}' ../par/test.par.'{role}'.txt"
    if subprocess.run(command, shell=True).returncode != 0:
        print(f"Failed to perform command {command}")
        exit(1)
    print("\n\n Finished GWAS \n\n")


def main():
    pass


if __name__ == "__main__":
    main()
