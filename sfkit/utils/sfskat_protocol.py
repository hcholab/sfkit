"""
Run the SF-SKAT protocol

SF-SKAT (https://github.com/swanhong/secure-skat) does not perform data preparation
itself: participants must have already run ``secure-rvas prepare`` out-of-band to
produce a ``prepared/`` directory tree, and register that directory's parent (the
tool's ``run_dir``) with sfkit. Role 0 is an auxiliary, data-free compute party
(like CP0 in SF-GWAS); role 1 is Cohort A; role 2 is Cohort B.
"""

import hashlib
import os
import random
import time

import tomlkit
from nacl.encoding import HexEncoder
from nacl.public import Box, PrivateKey, PublicKey

from sfkit.api import get_doc_ref_dict, update_firestore, website_send_file
from sfkit.utils import constants
from sfkit.utils.helper_functions import (
    condition_or_fail,
    copy_results_to_cloud_storage,
    copy_to_out_folder,
    install_go,
    run_command,
)
from sfkit.utils.sfgwas_helper_functions import boot_sfkit_proxy, to_float_int_or_bool
from sfkit.utils.sfgwas_protocol import sync_with_other_vms


def run_sfskat_protocol(role: str, demo: bool = False) -> None:
    print("\n\n Begin running SF-SKAT protocol \n\n")
    if not (constants.IS_DOCKER or constants.IS_INSTALLED_VIA_SCRIPT):
        install_sfskat()

    doc_ref_dict: dict = get_doc_ref_dict()
    ancestries = parse_list_param(doc_ref_dict["parameters"]["ancestries"]["value"], ["EUR"])

    if not demo:
        generate_shared_keys(int(role), ancestries)

    print("Begin updating config files")
    config_path = update_config(role)

    sync_with_other_vms(role, demo)
    start_sfskat(role, config_path)


def install_sfskat() -> None:
    update_firestore("update_firestore::task=Installing dependencies")
    print("Begin installing dependencies")

    install_go()

    if os.path.isdir("sf-skat"):
        print("sf-skat already exists")
    else:
        print("Installing sf-skat")
        run_command(["git", "clone", "https://github.com/swanhong/secure-skat.git", "sf-skat"])
        cwd = os.getcwd()
        os.chdir("sf-skat")
        run_command(["go", "build", "-o", "secure-rvas", "secure-rvas.go"])
        os.chdir(cwd)

    print("Finished installing dependencies")


def parse_list_param(value, default: list) -> list:
    if not value:
        return default
    items = [item.strip() for item in str(value).split(",") if item.strip()]
    return items or default


def get_registered_data_path() -> str:
    data_path_file = os.path.join(constants.SFKIT_DIR, "data_path.txt")
    with open(data_path_file, "r") as f:
        data_path = f.readline().rstrip()
    condition_or_fail(bool(data_path), "Data path not found in data_path.txt")
    return data_path


def get_run_dir(role: str) -> str:
    # Role 0 (auxiliary) holds no data and never registers a data_path; it just
    # needs a local working directory for secure-rvas to write metrics into.
    if role == "0":
        run_dir = os.path.join(constants.SFKIT_DIR, "skat_run")
        os.makedirs(run_dir, exist_ok=True)
        return run_dir
    return get_registered_data_path()


def shared_keys_root() -> str:
    return os.path.join(constants.SFKIT_DIR, "skat_shared_keys")


def generate_shared_keys(role: int, ancestries: list) -> None:
    """
    Derive the per-ancestry shared PRG keys secure-rvas expects
    (shared_key_global.bin and shared_key_{a}_{b}.bin for every pair
    involving this party), without any extra communication: each pairwise
    key is a Diffie-Hellman shared secret (deriving identically on both
    ends via NaCl Box), and the global key is deterministically seeded
    from CP0's public key, exactly as sfkit already does for SF-GWAS.
    """
    doc_ref_dict: dict = get_doc_ref_dict()
    update_firestore("update_firestore::task=Generating cryptographic keys")
    print("Generating shared keys...")

    private_key_path = os.path.join(constants.SFKIT_DIR, "my_private_key.txt")
    with open(private_key_path, "r") as f:
        my_private_key = PrivateKey(f.readline().rstrip().encode(), encoder=HexEncoder)

    pairwise_base_keys: dict = {}
    for i, other_username in enumerate(doc_ref_dict["participants"]):
        if i == role:
            continue
        other_public_key_str: str = doc_ref_dict["personal_parameters"][other_username]["PUBLIC_KEY"]["value"]
        while not other_public_key_str:
            print(f"No public key found for {other_username}.  Waiting...")
            time.sleep(5)
            doc_ref_dict = get_doc_ref_dict()
            other_public_key_str = doc_ref_dict["personal_parameters"][other_username]["PUBLIC_KEY"]["value"]
        other_public_key = PublicKey(other_public_key_str.encode(), encoder=HexEncoder)
        condition_or_fail(
            my_private_key != other_public_key,
            "Private and public keys must be different",
        )
        pairwise_base_keys[i] = Box(my_private_key, other_public_key).shared_key()

    cp0_username: str = doc_ref_dict["participants"][0]
    cp0_public_key_str: str = doc_ref_dict["personal_parameters"][cp0_username]["PUBLIC_KEY"]["value"]

    root = shared_keys_root()
    for ancestry in ancestries:
        ancestry_dir = os.path.join(root, ancestry)
        os.makedirs(ancestry_dir, exist_ok=True)

        random.seed(f"{cp0_public_key_str}|{ancestry}")
        global_key = random.getrandbits(256).to_bytes(32, "big")
        with open(os.path.join(ancestry_dir, "shared_key_global.bin"), "wb") as f:
            f.write(global_key)

        for other_role, base_key in pairwise_base_keys.items():
            derived = hashlib.sha256(base_key + ancestry.encode()).digest()
            a, b = sorted((role, other_role))
            with open(os.path.join(ancestry_dir, f"shared_key_{a}_{b}.bin"), "wb") as f:
                f.write(derived)

    print(f"Shared keys generated and saved to {root}.")


def update_config(role: str) -> str:
    """
    Build the flat run_config.toml that secure-rvas's ``party`` subcommand expects.
    Only fields that matter at MPC runtime (as opposed to ``prepare``, which sfkit
    does not invoke) are driven by study parameters; the rest are unused
    placeholders kept just to satisfy secure-rvas's config validation.
    """
    doc_ref_dict: dict = get_doc_ref_dict()
    pars = {**doc_ref_dict["parameters"], **doc_ref_dict["advanced_parameters"]}

    def scalar(key: str, default):
        raw = pars.get(key, {}).get("value", "")
        return to_float_int_or_bool(raw) if raw != "" else default

    ancestries = parse_list_param(pars.get("ancestries", {}).get("value"), ["EUR"])
    chromosomes = [int(c) for c in parse_list_param(pars.get("chromosomes", {}).get("value"), ["21", "22"])]
    masks = parse_list_param(pars.get("masks", {}).get("value"), ["LoF=HC"])
    phenotype_columns = parse_list_param(pars.get("phenotype_columns", {}).get("value"), ["phenotype1"])

    data = {
        "run_dir": get_run_dir(role),
        "chromosomes": chromosomes,
        # The following fields are only used by `secure-rvas prepare`, which sfkit
        # does not invoke (participants must already have run it out-of-band).
        # They're set to placeholders solely to satisfy config validation.
        "genotype": "unused",
        "gene_panel": "unused",
        "annotation": "unused",
        "phenotype": "unused",
        "covariate": "unused",
        "ancestry": "unused",
        "phenotype_id_column": "IID",
        "covariate_id_column": "IID",
        "covariate_column": "unused",
        "ancestry_id_column": "IID",
        "ancestry_column": "unused",
        "samples_per_cohort": 0,
        "sample_seed": 42,
        "role_seed": 42,
        "gene_selection": {"mode": "all"},
        # Operative fields, driven by study parameters.
        "phenotype_columns": phenotype_columns,
        "ancestries": ancestries,
        "num_cov": scalar("num_cov", 16),
        "masks": masks,
        "max_maf": scalar("max_maf", 0.01),
        "ckks": scalar("ckks", "PN14QP436S45"),
        "mpc_num_threads": scalar("mpc_num_threads", 2),
        "data_bits": scalar("data_bits", 60),
        "fractional_bits": scalar("fractional_bits", 30),
        "probes": scalar("probes", 30),
        "seed": scalar("seed", 42),
        "plink2_bin": "plink2",
        "binding_ipaddr": "0.0.0.0",
        "servers": {},
    }

    for i, participant in enumerate(doc_ref_dict["participants"]):
        ip_addr = doc_ref_dict["personal_parameters"][participant]["IP_ADDRESS"]["value"]
        ports: list = doc_ref_dict["personal_parameters"][participant]["PORTS"]["value"].split(",")

        server = {
            "ipaddr": "127.0.0.1" if constants.SFKIT_PROXY_ON else ip_addr,
            "ports": {},
        }
        for j, port in enumerate(ports):
            if port != "null" and i != j:
                server["ports"][f"party{j}"] = port
        data["servers"][f"party{i}"] = server

    config_path = os.path.join(constants.SFKIT_DIR, "skat_config.toml")
    with open(config_path, "w") as f:
        f.write(tomlkit.dumps(data))

    return config_path


def start_sfskat(role: str, config_path: str) -> None:
    update_firestore("update_firestore::task=Performing SF-SKAT protocol")
    print("\n\n starting SF-SKAT \n\n")

    sfkit_proxy = None
    if constants.SFKIT_PROXY_ON:
        sfkit_proxy = boot_sfkit_proxy(role, config_path)

    binary = (
        "secure-rvas"
        if (constants.IS_DOCKER or constants.IS_INSTALLED_VIA_SCRIPT)
        else os.path.join("sf-skat", "secure-rvas")
    )

    run_command(
        [
            binary,
            "party",
            "--config", config_path,
            "--party", role,
            "--shared-keys", shared_keys_root(),
        ],
        fail_message="Failed SF-SKAT protocol",
        role=role,
    )

    if sfkit_proxy:
        sfkit_proxy.terminate()

    print("\n\n Finished SF-SKAT \n\n")

    if role == "1":
        process_output_files(role)

    update_firestore("update_firestore::status=Finished protocol!")


def process_output_files(role: str) -> None:
    # NOTE: demo mode isn't supported for SF-SKAT (there's no bundled demo
    # dataset, since sfkit never runs `secure-rvas prepare` itself), so this
    # always reads the data path registered via `sfkit register_data`.
    doc_ref_dict: dict = get_doc_ref_dict()
    user_id: str = doc_ref_dict["participants"][int(role)]

    run_dir = get_registered_data_path()
    secure_dir = os.path.join(run_dir, "secure")
    metrics_dir = os.path.join(run_dir, "metrics")

    copy_to_out_folder([secure_dir, metrics_dir])

    if results_path := doc_ref_dict["personal_parameters"][user_id].get("RESULTS_PATH", {}).get("value", ""):
        copy_results_to_cloud_storage(role, results_path, secure_dir)

    send_results: str = doc_ref_dict["personal_parameters"][user_id].get("SEND_RESULTS", {}).get("value")
    if send_results == "Yes":
        pars = {**doc_ref_dict["parameters"], **doc_ref_dict["advanced_parameters"]}
        ancestries = parse_list_param(pars.get("ancestries", {}).get("value"), ["EUR"])
        for ancestry in ancestries:
            results_file = os.path.join(secure_dir, ancestry, "all_secure_results.tsv")
            if os.path.exists(results_file):
                with open(results_file, "rb") as f:
                    website_send_file(f, f"{ancestry}_all_secure_results.tsv")

    print("Finished processing output files")
