import subprocess
from sfkit.protocol.utils import constants


def get_authentication() -> tuple[str, str]:
    with open(constants.AUTH_FILE, "r") as f:
        email: str = f.readline().rstrip()
        study_title: str = f.readline().rstrip()
    return (email, study_title)


def run_command(command: str) -> None:
    if subprocess.run(command, shell=True, executable="/bin/bash").returncode != 0:
        print(f"Failed to perform command {command}")
        exit(1)
