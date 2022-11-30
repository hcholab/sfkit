import os
import subprocess

from sfkit.api import update_firestore
from sfkit.utils import constants


def authenticate_user() -> None:
    if not os.path.exists(constants.AUTH_KEY):
        print("You have not authenticated.  Please run 'sfkit auth' to authenticate.")
        exit(1)


def run_command(command: str) -> None:
    if subprocess.run(command, shell=True, executable="/bin/bash").returncode != 0:
        print(f"Failed to perform command {command}")
        exit(1)


def condition_or_fail(condition: bool, message: str = "The sfkit process has failed.") -> None:
    if not condition:
        message = f"FAILED - {message}"
        print(message)
        update_firestore(f"update_firestore::status={message}")
        exit(1)
