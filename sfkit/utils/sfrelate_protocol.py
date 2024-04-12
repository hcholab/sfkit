import os
import resource
import subprocess
import sys
import threading
import time
import traceback
from typing import List

import requests
import tomlkit

from sfkit.api import get_doc_ref_dict, update_firestore, website_send_file
from sfkit.utils import constants
from sfkit.utils.helper_functions import (
    copy_results_to_cloud_storage,
    copy_to_out_folder,
    install_go,
    run_command,
)
from sfkit.utils.sfgwas_helper_functions import to_float_int_or_bool
from sfkit.utils.sfgwas_protocol import generate_shared_keys, sync_with_other_vms


def run_sfrelate_protocol(role: str, demo: bool) -> None:
    if not (constants.IS_DOCKER or constants.IS_INSTALLED_VIA_SCRIPT):
        install_sfrelate()
    if not demo:
        generate_shared_keys(int(role), skip_cp0=True)
    print("Begin updating config files")
    update_config_local(role, demo)
    update_config_global(demo)
    make_missing_folders()
    sync_with_other_vms(role, demo, skip_cp0=True)
    start_sfrelate(role, demo)


def install_sfrelate() -> None:
    update_firestore("update_firestore::task=Installing dependencies")
    print("Begin installing dependencies")

    run_command(["sudo", "apt-get", "update"])
    run_command(["sudo", "apt-get", "upgrade", "-y"])
    run_command(
        ["sudo", "apt-get", "install", "git", "wget", "unzip", "python3", "python3-pip", "python3-venv", "snapd", "-y"]
    )

    # Increase the number of open files allowed
    soft, hard = 1_000_000, 1_000_000
    resource.setrlimit(resource.RLIMIT_NOFILE, (soft, hard))

    install_go()

    if os.path.isdir("sf-relate"):
        print("sf-relate already installed")
    else:
        print("Installing sf-relate")
        run_command(["git", "clone", "https://github.com/froelich/sf-relate.git"])
        os.chdir("sf-relate")
        run_command(["git", "checkout", "sf-kit"])
        run_command(["go", "get", "relativeMatch"])
        run_command(["go", "build"])
        run_command(["go", "test", "-c", "-o", "sf-relate"])
        os.chdir("..")

    print("Finished installing dependencies")


def update_config_local(role: str, demo: bool) -> None:
    if demo or role == "0":
        if role == "0":
            raise ValueError("Function should not be run for role 0.")
        return

    data_path_file = os.path.join(constants.SFKIT_DIR, "data_path.txt")
    try:
        with open(data_path_file, "r") as f:
            data_path = f.readline().strip()
    except IOError:
        raise FileNotFoundError(f"Data path file not found: {data_path_file}")

    if not data_path:
        raise ValueError("Data path not found in data_path.txt")

    files = [role] + (["0"] if role == "1" else [])

    for i in files:
        config_file_path = os.path.join(
            constants.EXECUTABLES_PREFIX, "sf-relate", "config", "demo", f"configLocal.Party{i}.toml"
        )
        try:
            with open(config_file_path, "r") as file:
                filedata = file.read()
            filedata = filedata.replace("notebooks/data/demo", data_path)
            with open(config_file_path, "w") as file:
                file.write(filedata)
        except IOError as e:
            raise IOError(f"Error processing file {config_file_path}: {e}")


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

        if i == 1:  # in sf-relate, party 1 also runs CP0
            data.get("servers", {}).get("party0", {})["ipaddr"] = "127.0.0.1" if constants.SFKIT_PROXY_ON else ip_addr

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
            ["python3", "notebooks/pgen_to_npy.py", "-PARTY", "1", "-FOLDER", "config/demo"],
            message="Party 1 Data Processing",
            env_vars=env_vars,
        )
    if demo or role == "2":
        run_protocol_command(
            ["python3", "notebooks/pgen_to_npy.py", "-PARTY", "2", "-FOLDER", "config/demo"],
            message="Party 2 Data Processing",
            env_vars=env_vars,
        )

    # run protocol
    threads: List[threading.Thread] = []
    exceptions: List[Exception] = []  # Shared structure for exceptions

    def thread_target(command, **kwargs):
        try:
            run_protocol_command(command, **kwargs)
        except Exception as e:
            exceptions.append((e, traceback.format_exc()))  # type: ignore

    if demo or role == "1":
        threads.append(
            threading.Thread(
                target=thread_target,
                kwargs={
                    "command": ["./sf-relate"],
                    "output_file": "config/demo/logs/X/test.txt",
                    "message": "MHE - Party 1",
                    "env_vars": env_vars | {"PID": "1"},
                },
            )
        )
        threads[-1].start()
    if demo or role == "0" or role == "1":  # role 1 as sfrelate doesn't actually need a CP0
        time.sleep(1)
        threads.append(
            threading.Thread(
                target=thread_target,
                kwargs={
                    "command": ["./sf-relate"],
                    "output_file": "config/demo/logs/Z/test.txt",
                    "message": "MHE - Party 0",
                    "env_vars": env_vars | {"PID": "0"},
                },
            )
        )
        threads[-1].start()
    if demo or role == "2":
        threads.append(
            threading.Thread(
                target=thread_target,
                kwargs={
                    "command": ["./sf-relate"],
                    "output_file": "config/demo/logs/Y/test.txt",
                    "message": "MHE - Party 2",
                    "env_vars": env_vars | {"PID": "2"},
                },
            )
        )
        threads[-1].start()

    for thread in threads:
        thread.join()

    # Check for exceptions
    if exceptions:
        for exc, tb in exceptions:  # type: ignore
            print(f"Error: {exc} with traceback {tb}")
        # Optionally, raise an exception or handle it as needed
        raise RuntimeError("One or more threads failed.")

    # post process
    if demo or role == "1":
        run_protocol_command(
            ["python3", "notebooks/step3_post_process.py", "-PARTY", "1", "-FOLDER", "config/demo/"],
            message="Post Processing - Party 1",
            env_vars=env_vars,
        )
    if demo or role == "2":
        run_protocol_command(
            ["python3", "notebooks/step3_post_process.py", "-PARTY", "2", "-FOLDER", "config/demo/"],
            message="Post Processing - Party 2",
            env_vars=env_vars,
        )

    print("Finished SF-Relate Protocol")

    if role != "0":
        process_output_files(role)

    update_firestore("update_firestore::status=Finished protocol!")


def handle_output(stream, write_to_file=None, print_stderr=False):
    for line in stream:
        if write_to_file:
            write_to_file.write(line)
            write_to_file.flush()
        if print_stderr:
            print(f"ERROR: {line}", end="", file=sys.stderr)
        else:
            print(line, end="")


def run_protocol_command(
    command_list: list,
    message: str = "",
    env_vars=None,
    output_file: str = "",
    cwd=f"{constants.EXECUTABLES_PREFIX}sf-relate",
):
    if not env_vars:
        env_vars = {}

    if message:
        update_firestore(f"update_firestore::task={message}")

    process_env = os.environ.copy()
    process_env.update(env_vars)

    print(f"Running command: {command_list} from {cwd}")

    with subprocess.Popen(
        command_list,
        env=process_env,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    ) as proc:
        file = open(f"{cwd}/{output_file}", "w") if output_file else None

        stdout_thread = threading.Thread(target=handle_output, args=(proc.stdout, file))
        stderr_thread = threading.Thread(target=handle_output, args=(proc.stderr, file, True))

        stdout_thread.start()
        stderr_thread.start()

        stdout_thread.join()
        stderr_thread.join()

        if file:
            file.close()

        proc.wait()
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, command_list)


def process_output_files(role: str) -> None:
    print("Processing output files")
    doc_ref_dict: dict = get_doc_ref_dict()
    user_id: str = doc_ref_dict["participants"][int(role)]

    out_path = f"{constants.EXECUTABLES_PREFIX}sf-relate/config/demo/out/raw"
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
    tar_url = "https://storage.googleapis.com/sfkit_1000_genomes/demo.tar.gz"
    tar_path = os.path.join(data_dir, "demo.tar.gz")

    print("Downloading Data")
    response = requests.get(tar_url, stream=True)
    with open(tar_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)

    print("Extracting Data using tar command")
    run_command(["tar", "-xvf", tar_path, "-C", data_dir])
