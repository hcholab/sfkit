import os
import shlex
import subprocess
from typing import List

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
            run_command("rm -f go1.22.0.linux-amd64.tar.gz")
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
            filedata = filedata.replace("PARA = 3", "PARA = 10")
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

    env_vars = {
        "t": "demo",
        "FOLDER": "config/demo/",
        "PYTHONUNBUFFERED": "TRUE",
    }

    if demo:
        download_and_extract_data()

    # preprocess data
    if demo or role == "1":
        run_protocol_command(
            "python3 notebooks/pgen_to_npy.py -PARTY 1 -FOLDER config/demo",
            message="party 1 data processing",
            env_vars=env_vars,
        )
    if demo or role == "2":
        run_protocol_command(
            "python3 notebooks/pgen_to_npy.py -PARTY 2 -FOLDER config/demo",
            message="party 2 data processing",
            env_vars=env_vars,
        )

    # run protocol
    processes = []
    if demo or role == "1":
        processes.append(
            run_protocol_command(
                "./goParty",
                output_file="config/demo/logs/X/test.txt",
                message="MHE - Party 1",
                env_vars=env_vars | {"PID": "1"},
                wait=False,
            )
        )
    if demo or role == "0":
        processes.append(
            run_protocol_command(
                "./goParty",
                output_file="config/demo/logs/Z/test.txt",
                message="MHE - Party 0",
                env_vars=env_vars | {"PID": "0"},
                wait=False,
            )
        )
    if demo or role == "2":
        processes.append(
            run_protocol_command(
                "./goParty",
                output_file="config/demo/logs/Y/test.txt",
                message="MHE - Party 2",
                env_vars=env_vars | {"PID": "2"},
                wait=False,
            )
        )

    for process in processes:
        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, process.args)

    # post process
    if demo or role == "1":
        run_protocol_command(
            "python3 notebooks/step3_post_process.py -PARTY 1 -FOLDER config/demo/",
            message="Post Processing - Party 1",
            env_vars=env_vars,
        )
    if demo or role == "2":
        run_protocol_command(
            "python3 notebooks/step3_post_process.py -PARTY 2 -FOLDER config/demo/",
            message="Post Processing - Party 2",
            env_vars=env_vars,
        )

    print("Finished SF-Relate Protocol")

    if role != "0":
        process_output_files(role)

    update_firestore("update_firestore::status=Finished protocol!")


def run_protocol_command(
    command: str,
    message: str = "",
    env_vars=None,
    output_file: str = "",
    wait=True,
    cwd=f"{constants.EXECUTABLES_PREFIX}sf-relate",
):
    if not env_vars:
        env_vars = {}

    full_env = os.environ.copy()
    full_env |= env_vars

    print(f"Running command: {command}")
    if message:
        update_firestore(f"update_firestore::task={message}")

    try:
        if output_file:
            with open(output_file, "w", buffering=1) as output:
                process = subprocess.Popen(
                    shlex.split(command), stdout=output, stderr=subprocess.STDOUT, env=full_env, cwd=cwd
                )
        else:
            process = subprocess.Popen(
                shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=full_env, cwd=cwd, text=True
            )
            if not wait:
                return process
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                print(f"Command failed with return code {process.returncode}")
                print(f"stdout: {stdout}")
                print(f"stderr: {stderr}")
                update_firestore(f"update_firestore::status=Failed command: {command}")
                raise subprocess.CalledProcessError(process.returncode, command, output=stdout, stderr=stderr)
            else:
                print("Command succeeded.")
                print(f"stdout: {stdout}")
                print(f"stderr: {stderr}")
    except Exception as e:
        print(f"Failed to execute command: {command}")
        print(e)
        update_firestore(f"update_firestore::status=Failed command: {command}")
        exit(1)


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


def download_and_extract_data():
    data_dir = os.path.join(constants.EXECUTABLES_PREFIX, "sf-relate", "notebooks", "data")
    os.makedirs(data_dir, exist_ok=True)

    run_protocol_command(
        "wget https://storage.googleapis.com/sfkit_1000_genomes/demo.tar.gz", message="Downloading Data", cwd=data_dir
    )

    run_protocol_command("tar -xvf demo.tar.gz", message="Extracting Data", cwd=data_dir)
