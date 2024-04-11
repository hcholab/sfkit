import os
import shutil
import subprocess

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from google.cloud import storage
from qmplot import manhattanplot
from scipy.stats import chi2

from sfkit.api import update_firestore
from sfkit.utils import constants


def authenticate_user() -> None:
    if not os.path.exists(constants.AUTH_KEY):
        print("You have not authenticated.  Please run 'sfkit auth' to authenticate.")
        exit(1)


def run_command(command_list: list, fail_message: str = "") -> None:
    with subprocess.Popen(
        command_list,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=dict(os.environ, PYTHONUNBUFFERED="1"),
        text=True,
        bufsize=1,
    ) as process:
        while process.stdout:
            if line := process.stdout.readline().strip():
                print(line)
            elif process.poll() is not None:
                break

    res = process.returncode
    if res != 0:
        print(f"FAILED - {command_list}")
        print(f"Return code: {res}")
        condition_or_fail(False, fail_message)


def condition_or_fail(condition: bool, message: str = "The sfkit process has failed.") -> None:
    if not condition:
        message = f"FAILED - {message}"
        print(message)
        update_firestore(f"update_firestore::status={message}")
        exit(0)  # 0 so that the wrapper doesn't override the status with a more generic error


def postprocess_assoc(
    new_assoc_file: str,
    assoc_file: str,
    pos_file: str,
    gkeep1_file: str,
    gkeep2_file: str,
    num_ind_total: int,
    num_cov: int,
) -> None:
    # new_assoc_file: Name of new assoc file
    # assoc_file: Name of original assoc file
    # pos_file: Path to pos.txt
    # gkeep1_file: Path to gkeep1.txt
    # gkeep2_file: Path to gkeep2.txt
    # num_ind_total: Total number of individuals
    # num_cov: Number of covariates

    # Combine filters
    gkeep1 = np.loadtxt(gkeep1_file, dtype=bool)
    if gkeep2_file != "":
        gkeep2 = np.loadtxt(gkeep2_file, dtype=bool)
        gkeep1[gkeep1] = gkeep2

    # Load and check dimension of output association stats
    assoc = np.loadtxt(assoc_file)
    assert len(assoc) == gkeep1.sum()

    # Calculate p-values
    t2 = (assoc**2) * (num_ind_total - num_cov) / (1 - assoc**2 + 1e-10)
    log10p = np.log10(chi2.sf(t2, df=1))

    # Append SNP position information and write to a new file
    lineno = 0
    assoc_idx = 0

    with open(new_assoc_file, "w") as out:
        out.write("\t".join(["#CHROM", "POS", "R", "LOG10P"]) + "\n")

        for line in open(pos_file):
            pos = line.strip().split()

            if gkeep1[lineno]:
                out.write(pos[0] + "\t" + pos[1] + "\t" + str(assoc[assoc_idx]) + "\t" + str(log10p[assoc_idx]) + "\n")
                assoc_idx += 1

            lineno += 1


def plot_assoc(plot_file: str, new_assoc_file: str) -> None:
    # Load postprocessed assoc file and convert p-values
    tab = pd.read_table(new_assoc_file)
    tab["P"] = 10 ** tab["LOG10P"]

    # Create a Manhattan plot
    plt.figure()
    manhattanplot(
        data=tab,
        suggestiveline=None,  # type: ignore
        genomewideline=None,  # type: ignore
        marker=".",
        xticklabel_kws={"rotation": "vertical"},  # set vertical or any other degrees as you like.
    )
    plt.savefig(plot_file)


def copy_results_to_cloud_storage(role: str, data_path: str, output_directory: str) -> None:
    os.makedirs(output_directory, exist_ok=True)
    if "sfgwas" in output_directory:
        shutil.copyfile(
            f"{constants.EXECUTABLES_PREFIX}sfgwas/cache/party{role}/Qpc.txt", f"{output_directory}/Qpc.txt"
        )

    try:
        storage_client = storage.Client()
        bucket_name, prefix = data_path.split("/", 1)
        bucket = storage_client.bucket(bucket_name)
        for file in os.listdir(output_directory):
            blob = bucket.blob(f"{prefix}/out/party{role}/{file}")
            blob.upload_from_filename(f"{output_directory}/{file}")
        print(f"Successfully uploaded results from {output_directory} to gs://{data_path}/out/party{role}")
    except Exception as e:
        print("Failed to upload results to cloud storage")
        print(e)


def copy_to_out_folder(relevant_paths: list) -> None:
    """
    Overwrite the contents of the out folder with the files/folders in relevant_paths
    """
    if not os.path.exists(constants.OUT_FOLDER):
        os.makedirs(constants.OUT_FOLDER)

    for path in relevant_paths:
        if os.path.exists(path):
            destination = f"{constants.OUT_FOLDER}/{os.path.basename(path)}"
            if os.path.isfile(path):
                shutil.copy2(path, destination)
            elif os.path.isdir(path):
                if os.path.exists(destination):
                    shutil.rmtree(destination)
                shutil.copytree(path, destination)


def install_go():
    print("Installing go")
    run_command(["sudo", "snap", "install", "go", "--classic"])
    os.environ["PATH"] += f"{os.pathsep}/snap/bin"
    with open(os.path.expanduser("~/.bashrc"), "a") as file:
        file.write("\nexport PATH=$PATH:/snap/bin\n")
    run_command(["go", "version"])
    print("Finished installing go")
