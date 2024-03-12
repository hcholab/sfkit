import os
import subprocess

import tomlkit

from sfkit.api import get_doc_ref_dict, update_firestore, website_send_file
from sfkit.utils import constants
from sfkit.utils.helper_functions import (
    condition_or_fail,
    copy_results_to_cloud_storage,
    copy_to_out_folder,
    run_command,
)
from sfkit.utils.sfgwas_helper_functions import to_float_int_or_bool
from sfkit.utils.sfgwas_protocol import generate_shared_keys, sync_with_other_vms


def run_sfrelate_protocol(role: str, demo: bool) -> None:
    if not (constants.IS_DOCKER or constants.IS_INSTALLED_VIA_SCRIPT):
        install_sfrelate()
    if not demo:
        generate_shared_keys(int(role))
    print("Begin updating config files")
    update_config_local(role, demo)
    update_config_global(demo)
    make_missing_folders()
    sync_with_other_vms(role, demo)
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


def update_config_local(role: str, demo) -> None:
    config_file_path = f"{constants.EXECUTABLES_PREFIX}sf-relate/config/demo/configLocal.Party{role}.toml"

    with open(config_file_path, "r") as file:
        filedata = file.read()

    if role != "0" and not demo:
        with open(os.path.join(constants.SFKIT_DIR, "data_path.txt"), "r") as f:
            data_path = f.readline().rstrip()
        if data_path:
            filedata = filedata.replace("notebooks/data/demo", data_path)

    with open(config_file_path, "w") as file:
        file.write(filedata)


def update_config_global(demo) -> None:
    print("Updating configGlobal.toml")
    doc_ref_dict: dict = get_doc_ref_dict()
    file_path = f"{constants.EXECUTABLES_PREFIX}sf-relate/config/demo/configGlobal.toml"

    if demo:
        with open(file_path, "r") as file:
            filedata = file.read()
            filedata = filedata.replace("PARA = 1", "PARA = 10")
            filedata = filedata.replace("5110", "3110")
        with open(file_path, "w") as file:
            file.write(filedata)
        return

    with open(file_path, "r") as file:
        data = tomlkit.parse(file.read())

    data["PARA"] = 10

    # Update the ip addresses and ports
    for i, participant in enumerate(doc_ref_dict["participants"]):
        ip_addr = doc_ref_dict["personal_parameters"][participant]["IP_ADDRESS"]["value"]
        data.get("servers", {}).get(f"party{i}", {})["ipaddr"] = "127.0.0.1" if constants.SFKIT_PROXY_ON else ip_addr

        ports: list = doc_ref_dict["personal_parameters"][participant]["PORTS"]["value"].split(",")
        for j, port in enumerate(ports):
            if port != "null" and i != j:
                data.get("servers", {}).get(f"party{i}", {}).get("ports", {})[f"party{j}"] = port

    data["shared_keys_path"] = constants.SFKIT_DIR

    # shared and advanced parameters
    pars = {**doc_ref_dict["parameters"], **doc_ref_dict["advanced_parameters"]}
    for key, value in pars.items():
        if key in data:
            data[key] = to_float_int_or_bool(value["value"])

    with open(file_path, "w") as file:
        file.write(tomlkit.dumps(data))


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

    os.environ["t"] = "demo"
    os.environ["FOLDER"] = "config/demo/"
    protocol_steps = []
    if demo:
        protocol_steps += [
            (
                "cd notebooks/data && wget https://storage.googleapis.com/sfkit_1000_genomes/demo.tar.gz && tar -xvf demo.tar.gz",
                "Getting Data",
            )
        ]
    if demo or role == "1":
        protocol_steps += [
            ("python3 notebooks/pgen_to_npy.py -PARTY 1 -FOLDER config/demo", "party 1 data processing")
        ]
    if demo or role == "2":
        protocol_steps += [
            ("python3 notebooks/pgen_to_npy.py -PARTY 2 -FOLDER config/demo", "party 2 data processing")
        ]
    if demo:
        command = (
            f"(cd {constants.EXECUTABLES_PREFIX}sf-relate && PID=1 ./goParty > config/demo/logs/X/test.txt) & "
            f"(cd {constants.EXECUTABLES_PREFIX}sf-relate && PID=0 ./goParty > config/demo/logs/Z/test.txt) & "
            f"(cd {constants.EXECUTABLES_PREFIX}sf-relate && PID=2 ./goParty > config/demo/logs/Y/test.txt) & "
            "wait $(jobs -p)"
        )
        protocol_steps += [(command, "MHE - All Parties")]
    else:
        if role == "0":
            protocol_steps += [
                ("sleep 1 && PID=0 ./goParty > config/demo/logs/Z/test.txt", "MHE - Party 0"),
            ]
        if role == "1":
            protocol_steps += [
                ("sleep 1 && PID=1 ./goParty > config/demo/logs/X/test.txt", "MHE - Party 1"),
            ]
        if role == "2":
            protocol_steps += [
                ("sleep 1 && PID=2 ./goParty > config/demo/logs/Y/test.txt", "MHE - Party 2"),
            ]
    if demo or role == "1":
        protocol_steps += [
            ("python3 notebooks/step3_post_process.py -PARTY 1 -FOLDER config/demo/", "Post Processing - Party 1"),
        ]
    if demo or role == "2":
        protocol_steps += [
            ("python3 notebooks/step3_post_process.py -PARTY 2 -FOLDER config/demo/", "Post Processing - Party 2"),
        ]

    for command, message in protocol_steps:
        full_command = f"export PYTHONUNBUFFERED=TRUE && cd {constants.EXECUTABLES_PREFIX}sf-relate && {command}"
        print(f"Running command: {full_command}")
        if message:
            update_firestore(f"update_firestore::task={message}")
        try:
            res = subprocess.run(full_command, shell=True, executable="/bin/bash")
            if res.returncode != 0:
                raise Exception(res.stderr)  # sourcery skip: raise-specific-error
            print(f"Finished command: {full_command}")
        except Exception as e:
            print(f"Failed command: {full_command}")
            print(e)
            update_firestore(f"update_firestore::status=Failed command: {full_command}")
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
