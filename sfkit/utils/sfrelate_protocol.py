import os
import subprocess
from sfkit.api import update_firestore
from sfkit.utils.helper_functions import condition_or_fail, run_command
from sfkit.utils.sfgwas_protocol import sync_with_other_vms
from sfkit.utils import constants


def run_sfrelate_protocol(role: str, demo: bool) -> None:
    # install for pip version?
    if not (constants.IS_DOCKER or constants.IS_INSTALLED_VIA_SCRIPT):
        install_sfrelate()
    # TODO: if not demo, update config files
    # sync_with_other_vms(role, demo)
    update_test_param()
    update_config_global()
    start_sfrelate(role, demo)


def install_sfrelate() -> None:
    update_firestore("update_firestore::task=Installing dependencies")
    print("Begin installing dependencies")

    run_command("sudo apt-get update && sudo apt-get upgrade -y")
    run_command("sudo apt-get install git wget unzip python3 python3-pip python3-venv -y")
    run_command("ulimit -n 1000000")

    if os.path.isdir("/usr/local/go"):
        print("go already installed")
    else:
        print("Installing go")
        max_retries = 3
        retries = 0
        while retries < max_retries:
            run_command("rm -f https://golang.org/dl/go1.22.0.linux-amd64.tar.gz")
            run_command("wget -nc https://golang.org/dl/go1.22.0.linux-amd64.tar.gz")
            run_command("sudo rm -rf /usr/local/go && sudo tar -C /usr/local -xzf go1.22.0.linux-amd64.tar.gz")
            if os.path.isdir("/usr/local/go"):
                break
            retries += 1
        if not os.path.isdir("/usr/local/go"):
            condition_or_fail(False, "go failed to install")
        os.environ["PATH"] += f"{os.pathsep}/usr/local/go/bin"
        run_command("go version")
        print("go successfully installed")

    if os.path.isdir("sf-relate"):
        print("sf-relate already installed")
    else:
        print("Installing sf-relate")
        run_command("git clone https://github.com/froelich/sf-relate.git")
        run_command("cd sf-relate && git checkout sf-kit")
        run_command("cd sf-relate && go get relativeMatch")
        run_command("cd sf-relate && go build")

    print("Finished installing dependencies")


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
            "make party1 -j2 &",
            "make party2",
        ]
        messages = ["Getting Data", "Step 0: Sampling Shared Parameters", "", "Step 1: Hashing", "", "Step 2: MHE", ""]
        for i, protocol_command in enumerate(protocol_commands):
            command = (
                f"export PYTHONUNBUFFERED=TRUE && cd {constants.EXECUTABLES_PREFIX}sf-relate && {protocol_command}"
            )
            print(f"Running command: {command}")
            if messages[i]:
                update_firestore(f"update_firestore::task={messages[i]}")
            try:
                res = subprocess.run(command, shell=True, executable="/bin/bash")
                if res.returncode != 0:
                    raise Exception(res.stderr)  # sourcery skip: raise-specific-error
                print(f"Finished command: {command}")
            except Exception as e:
                print(f"Failed command: {command}")
                print(e)
                update_firestore(f"update_firestore::status=Failed command: {command}")
                return

    print("Finished SF-Relate Protocol")
    update_firestore("update_firestore::status=Finished protocol!")

    # if role == "0":
    #     # update_firestore("update_firestore::status=Finished protocol!")
    #     return

    # TODO: send results and/or graphs back to the website
