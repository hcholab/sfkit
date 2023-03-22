import os
import re
import select
import shutil
import subprocess
from typing import Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import requests
from bs4 import BeautifulSoup

from sfkit.api import get_doc_ref_dict, update_firestore, website_send_file
from sfkit.utils import constants
from sfkit.utils.helper_functions import (
    condition_or_fail,
    copy_results_to_cloud_storage,
    plot_assoc,
    postprocess_assoc,
)


def get_file_paths() -> Tuple[str, str]:
    with open(os.path.join(constants.SFKIT_DIR, "data_path.txt"), "r") as f:
        geno_file_prefix = f.readline().rstrip()
        data_path = f.readline().rstrip()
    return geno_file_prefix, data_path


def use_existing_config(role: str, doc_ref_dict: dict) -> None:
    print("Using blocks with config files")
    if role != "0":
        _, data_path = get_file_paths()

        source = f"{data_path}/p{role}/for_sfgwas"
        destination = "sfgwas/for_sfgwas"
        move(source, destination)

    config = doc_ref_dict["description"].split(constants.BLOCKS_MODE)[1]

    source = f"sfgwas/config/blocks/{config}"
    destination = "sfgwas/config/gwas"
    move(source, destination)


def move(source: str, destination: str) -> None:
    print(f"Moving {source} to {destination}...")
    shutil.rmtree(destination, ignore_errors=True)
    shutil.move(source, destination)


def run_sfgwas_with_task_updates(command: str, protocol: str, demo: bool, role: str) -> None:
    doc_ref_dict: dict = get_doc_ref_dict()
    num_power_iters: int = 2 if demo else int(doc_ref_dict["advanced_parameters"]["num_power_iters"]["value"])

    task_updates = constants.task_updates(num_power_iters)
    transform = constants.transform(num_power_iters)

    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, executable="/bin/bash"
    )

    waiting_time = 86_400
    prev_task = ""
    current_task = task_updates.pop(0)
    while process.poll() is None:
        rlist, _, _ = select.select([process.stdout, process.stderr], [], [], waiting_time)

        if not rlist:
            if waiting_time == 86_400:
                print("WARNING: sfgwas has been stalling for 24 hours. Killing process.")
                condition_or_fail(False, f"{protocol} protocol has been stalling for 24 hours. Killing process.")
            process.kill()
            update_firestore(f"update_firestore::task={transform[current_task]} completed")
            return

        for stream in rlist:
            line = stream.readline().decode("utf-8").strip()
            print(line)
            if current_task in line:
                if prev_task:
                    update_firestore(f"update_firestore::task={transform[prev_task]} completed")
                update_firestore(f"update_firestore::task={transform[current_task]}")
                if task_updates:
                    prev_task = current_task
                    current_task = task_updates.pop(0)
            elif "Output collectively decrypted and saved to" in line or (
                protocol == "PCA" and f"Saved data to cache/party{role}/Qpc.txt" in line
            ):
                waiting_time = 30

            check_for_failure(command, protocol, process, stream, line)

    process.wait()

    update_firestore(f"update_firestore::task={transform[current_task]} completed")


def check_for_failure(command: str, protocol: str, process: subprocess.Popen, stream: list, line: str) -> None:
    if (
        stream == process.stderr
        and line
        and not line.startswith("W :")
        and "[watchdog] gc finished" not in line
        and "warning:" not in line
    ):
        print(f"FAILED - {command}")
        print(f"Stderr: {line}")
        condition_or_fail(False, f"Failed {protocol} protocol")


def post_process_results(role: str, demo: bool, protocol: str) -> None:
    doc_ref_dict: dict = get_doc_ref_dict()
    user_id: str = doc_ref_dict["participants"][int(role)]
    send_results: str = doc_ref_dict["personal_parameters"][user_id].get("SEND_RESULTS", {}).get("value")

    if protocol == "SFGWAS":
        make_new_assoc_and_manhattan_plot(doc_ref_dict, demo, role)
    elif protocol == "PCA":
        make_pca_plot(role)

    # copy results to cloud storage
    if doc_ref_dict["setup_configuration"] == "website":
        data_path = doc_ref_dict["personal_parameters"][user_id]["DATA_PATH"]["value"]
        if demo and not data_path:
            study_title: str = doc_ref_dict["title"].replace(" ", "").lower()
            data_path = f"sfkit_example_data/demo/{study_title}"
        copy_results_to_cloud_storage(role, data_path, f"sfgwas/out/party{role}")

    if protocol == "SFGWAS":
        if send_results == "Yes" and doc_ref_dict["setup_configuration"] == "website":
            with open(f"sfgwas/out/party{role}/new_assoc.txt", "r") as f:
                website_send_file(f, "new_assoc.txt")

            with open(f"sfgwas/out/party{role}/manhattan.png", "rb") as f:
                website_send_file(f, "manhattan.png")

            update_firestore("update_firestore::status=Finished protocol!")
        else:
            update_firestore(
                "update_firestore::status=Finished protocol! You can view the results in your cloud storage bucket or on your machine."
            )
    elif protocol == "PCA":
        if send_results == "Yes" and doc_ref_dict["setup_configuration"] == "website":
            with open(f"sfgwas/cache/party{role}/Qpc.txt", "r") as f:
                website_send_file(f, "Qpc.txt")

            with open(f"sfgwas/out/party{role}/pca_plot.png", "rb") as f:
                website_send_file(f, "pca_plot.png")

            update_firestore("update_firestore::status=Finished protocol!")
        else:
            update_firestore(
                "update_firestore::status=Finished protocol! You can view the results in your cloud storage bucket or on your machine."
            )

    update_firestore(f"update_firestore::task=Running {protocol} protocol completed")


def make_pca_plot(role: str) -> None:
    pcs = np.loadtxt(f"sfgwas/cache/party{role}/Qpc.txt", delimiter=",")
    plt.scatter(pcs[0], pcs[1])
    plt.xlabel("PC1")
    plt.ylabel("PC2")
    plt.savefig(f"sfgwas/out/party{role}/pca_plot.png")


def make_new_assoc_and_manhattan_plot(doc_ref_dict: dict, demo: bool, role: str) -> None:
    # sourcery skip: assign-if-exp, introduce-default-else, swap-if-expression
    num_inds_total = 2000
    if not demo:
        num_inds_total = sum(
            int(doc_ref_dict["personal_parameters"][user]["NUM_INDS"]["value"])
            for user in doc_ref_dict["participants"]
        )
    num_covs = int(doc_ref_dict["parameters"]["num_covs"]["value"])

    snp_pos_path = f"sfgwas/example_data/party{role}/snp_pos.txt"
    if not demo:
        with open(os.path.join(constants.SFKIT_DIR, "data_path.txt"), "r") as f:
            f.readline()
            data_path = f.readline().rstrip()
            snp_pos_path = f"{data_path}/snp_pos.txt"

    postprocess_assoc(
        f"sfgwas/out/party{role}/new_assoc.txt",
        f"sfgwas/out/party{role}/assoc.txt",
        snp_pos_path,
        f"sfgwas/cache/party{role}/gkeep.txt",
        "",
        num_inds_total,
        num_covs,
    )
    plot_assoc(f"sfgwas/out/party{role}/manhattan.png", f"sfgwas/out/party{role}/new_assoc.txt")


def to_float_int_or_bool(string: str) -> Union[float, int, bool, str]:
    if string.lower() in {"true", "false"}:
        return string.lower() == "true"
    try:
        return int(string)
    except ValueError:
        try:
            return float(string)
        except ValueError:
            return string


def get_plink2_download_link() -> str:
    """
    Scrapes the PLINK 2.0 website for the current Alpha download link for Plink2 for Linux AVX2 Intel.

    Returns:
        The download link for the current Alpha version of Plink2 for Linux AVX2 Intel.
    """

    url = "https://www.cog-genomics.org/plink/2.0/"

    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    if link := soup.find(
        "a",
        href=re.compile(r"^https://s3.amazonaws.com/plink2-assets/.*plink2_linux_avx2_.*\.zip$"),
    ):
        return link.get("href")  # type: ignore
    else:
        return "https://s3.amazonaws.com/plink2-assets/alpha3/plink2_linux_avx2_20221024.zip"
