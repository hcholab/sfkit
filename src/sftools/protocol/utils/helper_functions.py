import subprocess


def run_shell_command(command: str) -> None:
    if subprocess.run(command, shell=True).returncode != 0:
        print(f"Failed to perform command {command}")
        exit(1)
