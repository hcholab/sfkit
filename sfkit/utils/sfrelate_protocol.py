import os
import subprocess

from sfkit.api import get_doc_ref_dict, update_firestore, website_send_file
from sfkit.utils import constants
from sfkit.utils.helper_functions import (
    condition_or_fail,
    copy_results_to_cloud_storage,
    copy_to_out_folder,
    run_command,
)
from sfkit.utils.sfgwas_protocol import sync_with_other_vms


def run_sfrelate_protocol(role: str, demo: bool) -> None:
    # install for pip version?
    if not (constants.IS_DOCKER or constants.IS_INSTALLED_VIA_SCRIPT):
        install_sfrelate()
    # TODO: if not demo, update config files
    # sync_with_other_vms(role, demo)
    update_XYZ_local()  # TODO: should eventually just update sf-relate repo directly
    update_test_param()
    update_config_global()
    make_missing_folders()
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
        run_command("export GOCACHE=~/.cache/go-build")
        run_command("go version")
        print("go successfully installed")

    if os.path.isdir("sf-relate"):
        print("sf-relate already installed")
    else:
        print("Installing sf-relate")
        run_command("git clone https://github.com/froelich/sf-relate.git")
        run_command("cd sf-relate && git checkout sf-kit")
        run_command("cd sf-relate && go get relativeMatch")
        run_command("cd sf-relate && go build && go test -c -o goParty")

    print("Finished installing dependencies")


def update_XYZ_local() -> None:
    for L in "XYZ":
        file_path = f"{constants.EXECUTABLES_PREFIX}sf-relate/{L}_local.sh"
        with open(file_path, "r") as file:
            filedata = file.read()
        filedata = filedata.replace("| tee /dev/tty ", "")
        with open(file_path, "w") as file:
            file.write(filedata)


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


def make_missing_folders() -> None:
    for L in "XYZ":
        os.makedirs(f"{constants.EXECUTABLES_PREFIX}sf-relate/config/demo/logs/{L}", exist_ok=True)
    os.makedirs(f"{constants.EXECUTABLES_PREFIX}sf-relate/config/demo/out/raw", exist_ok=True)


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
            "cd notebooks/data && wget https://storage.googleapis.com/sfkit_1000_genomes/demo.tar.gz && tar -xvf demo.tar.gz",
            "python3 notebooks/pgen_to_npy.py -PARTY 1 -FOLDER config/demo",
            "python3 notebooks/pgen_to_npy.py -PARTY 2 -FOLDER config/demo",
            "bash X_local.sh &",
            "sleep 1 && bash Y_local.sh &",
            "sleep 1 && bash Z_local.sh",
        ]
        messages = ["Getting Data", "party 1 data processing", "party 2 data processing", "Step 2: MHE", "", ""]
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

    if role != "0":
        process_output_files(role)

    update_firestore("update_firestore::status=Finished protocol!")


def process_output_files(role: str) -> None:
    print("Processing output files")
    doc_ref_dict: dict = get_doc_ref_dict()
    user_id: str = doc_ref_dict["participants"][int(role)]

    out_path = f"{constants.EXECUTABLES_PREFIX}sf-relate/out/demo"
    copy_to_out_folder([out_path])

    if results_path := doc_ref_dict["personal_parameters"][user_id].get("RESULTS_PATH", {}).get("value", ""):
        copy_results_to_cloud_storage(role, results_path, out_path)

    send_results: str = doc_ref_dict["personal_parameters"][user_id].get("SEND_RESULTS", {}).get("value")
    if send_results == "Yes":
        with open(f"{out_path}/0_0_party{role}.csv", "rb") as file:
            website_send_file(file, f"0_0_party{role}.csv")

    print("Finished processing output files")
