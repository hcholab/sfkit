import subprocess
from sfkit.api import update_firestore
from sfkit.utils.sfgwas_protocol import sync_with_other_vms
from sfkit.utils import constants


def run_sfrelate_protocol(role: str, demo: bool) -> None:
    # install for pip version?
    # TODO: if not demo, update config files
    # sync_with_other_vms(role, demo)
    update_test_param()
    update_config_global()
    start_sfrelate(role, demo)


def update_test_param() -> None:
    file_path = f"{constants.EXECUTABLES_PREFIX}sf-relate/test_param.sh"
    with open(file_path, "r") as file:
        filedata = file.read()
    filedata = filedata.replace("export PARA=1", "export PARA=10")
    with open(file_path, "w") as file:
        file.write(filedata)


def update_config_global() -> None:
    file_path = f"{constants.EXECUTABLES_PREFIX}sf-relate/config/demo/configGlobal.toml"
    with open(file_path, "r") as file:
        filedata = file.read()
    filedata = filedata.replace("5110", "3110")
    with open(file_path, "w") as file:
        file.write(filedata)


def start_sfrelate(role: str, demo: bool) -> None:
    update_firestore("update_firestore::task=Initiating Protocol")
    print("Beginning SF-Relate Protocol")

    if constants.SFKIT_PROXY_ON:
        print("sfkit-proxy not yet implemented for SF-Relate")
        # TODO: modify boot_sfkit_proxy, and possibly the proxy itself to be compatible with SF-Relate
        # boot_sfkit_proxy(role=role, )

    # TODO: run the actual protocol
    if demo:
        protocol_commands = [
            "cd notebooks && wget https://storage.googleapis.com/sfkit_1000_genomes/trial.tar.gz && tar -xvf trial.tar.gz",
            "cd notebooks && python3 step0a_sample_hash_randomness.py -out trial -maf trial/maf -pos trial/pos -gmap trial/gmap -enclen 80 -N 204928 -k 8 -seglen 8 -steplen 4 -l 4",
            "cd notebooks && python3 step0b_sample_SNPs.py -M 145181 -s 0.7 -out trial/sketched",
            "cd notebooks && python3 step1_hashing.py -n 1601 -param trial -out trial/party1/table -hap trial/party1/haps -L 3",
            "cd notebooks && python3 step1_hashing.py -n 1601 -param trial -out trial/party2/table -hap trial/party2/haps -L 3",
            "make party1 -j2 & make party2",
        ]
        messages = ["Getting Data", "Step 0: Sampling Shared Parameters", "", "Step 1: Hashing", "", "Step 2: MHE"]
        for i, protocol_command in enumerate(protocol_commands):
            command = (
                f"export PYTHONUNBUFFERED=TRUE && cd {constants.EXECUTABLES_PREFIX}sf-relate && {protocol_command}"
            )
            print(f"Running command: {command}")
            if messages[i]:
                update_firestore(f"update_firestore::task={messages[i]}")
            subprocess.run(command, shell=True, executable="/bin/bash")
            print(f"Finished command: {command}")

    print("Finished SF-Relate Protocol")
    update_firestore("update_firestore::status=Finished protocol!")

    # if role == "0":
    #     # update_firestore("update_firestore::status=Finished protocol!")
    #     return

    # TODO: send results and/or graphs back to the website
