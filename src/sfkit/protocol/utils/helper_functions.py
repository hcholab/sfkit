import os
import subprocess

from sfkit.protocol.utils import constants


def authenticate_user() -> None:
    if not os.path.exists(constants.AUTH_KEY):
        print("You have not authenticated.  Please run 'sfkit auth' to authenticate.")
        exit(1)


def run_command(command: str) -> None:
    if subprocess.run(command, shell=True, executable="/bin/bash").returncode != 0:
        print(f"Failed to perform command {command}")
        exit(1)
