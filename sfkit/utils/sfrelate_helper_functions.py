import os
import shutil
import subprocess
import tarfile

import requests

from sfkit.utils.helper_functions import condition_or_fail


def install_go() -> None:
    go_installed_dir = "/usr/local/go"
    go_tarball_url = "https://golang.org/dl/go1.22.0.linux-amd64.tar.gz"
    go_tarball_path = "go1.22.0.linux-amd64.tar.gz"
    max_retries = 3

    if os.path.isdir(go_installed_dir):
        print("go already installed")
    else:
        print("Installing go")
        retries = 0
        while retries < max_retries:
            try:
                if os.path.exists(go_tarball_path):
                    os.remove(go_tarball_path)
                print("Downloading Go tarball...")
                response = requests.get(go_tarball_url)
                with open(go_tarball_path, "wb") as f:
                    f.write(response.content)
                print("Extracting Go tarball...")
                shutil.rmtree(go_installed_dir, ignore_errors=True)
                with tarfile.open(go_tarball_path) as tar:
                    tar.extractall(path="/usr/local")
                if os.path.isdir(go_installed_dir):
                    break
            except Exception as e:
                print(f"Attempt {retries + 1} failed with error: {e}")
            finally:
                retries += 1
        if not os.path.isdir(go_installed_dir):
            condition_or_fail(False, "go failed to install")
        else:
            print("go successfully installed")
            os.environ["PATH"] += f"{os.pathsep}/usr/local/go/bin"
            os.environ["GOCACHE"] = os.path.expanduser("~/.cache/go-build")
            try:
                subprocess.check_call(["go", "version"])
            except subprocess.CalledProcessError as e:
                print(f"Error verifying Go installation: {e}")
