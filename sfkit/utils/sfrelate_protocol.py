import subprocess
from sfkit.api import update_firestore
from sfkit.utils.sfgwas_protocol import sync_with_other_vms
from sfkit.utils import constants


def run_sfrelate_protocol(role: str, demo: bool) -> None:
    # install for pip version?
    # TODO: if not demo, update config files
    sync_with_other_vms(role, demo)
    start_sfrelate(role, demo)


def start_sfrelate(role: str, demo: bool) -> None:
    update_firestore("update_firestore::task=Initiating Protocol")
    print("Beginning SF-Relate Protocol")

    if constants.SFKIT_PROXY_ON:
        print("sfkit-proxy not yet implemented for SF-Relate")
        # TODO: modify boot_sfkit_proxy, and possibly the proxy itself to be compatible with SF-Relate
        # boot_sfkit_proxy(role=role, )

    # TODO: run the actual protocol
    protocol_commands = [
        "bash 0_prepare_1KG.sh",
        "bash 1_hashing.sh",
        "bash 2_sketch.sh",
        "bash 3_run_MHE.sh",
        "bash 4_verify_output.sh",
    ]
    for protocol_command in protocol_commands:
        command = f"export PYTHONUNBUFFERED=TRUE && cd {constants.EXECUTABLES_PREFIX}sf-relate && {protocol_command}"
        print(f"Running command: {command}")
        subprocess.run(command, shell=True, executable="/bin/bash")
        print(f"Finished command: {command}")

    print("Finished SF-Relate Protocol")

    if role == "0":
        update_firestore("update_firestore::status=Finished protocol!")
        return

    # TODO: send results and/or graphs back to the website
