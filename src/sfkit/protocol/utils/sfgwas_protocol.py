import os
import random
import time

import toml
from nacl.encoding import HexEncoder
from nacl.public import Box, PrivateKey, PublicKey
from sfkit.api import get_doc_ref_dict
from sfkit.protocol.utils import constants
from sfkit.protocol.utils.helper_functions import run_command


def run_sfgwas_protocol(role: str, phase: str = "") -> None:
    install_sfgwas()
    generate_shared_keys(int(role))
    update_config_files(role, phase)
    build_sfgwas()
    start_sfgwas(role)


def install_sfgwas() -> None:
    print("Begin installing dependencies")
    commands = [
        # "sudo apt-get update -y",
        # "sudo apt-get install python3-pip wget git zip unzip golang -y",
        "wget -nc https://golang.org/dl/go1.18.1.linux-amd64.tar.gz",
        "mkdir -p ~/.local/bin && mkdir -p ~/.local/lib",
        "tar -C ~/.local/lib -xzf go1.18.1.linux-amd64.tar.gz && mv ~/.local/lib/go/bin/go ~/.local/bin/go",
        "wget -nc https://s3.amazonaws.com/plink2-assets/alpha3/plink2_linux_avx2_20220603.zip",
        "unzip -o plink2_linux_avx2_20220603.zip -d ~/.local/bin",
        "echo 'export PYTHONUNBUFFERED=TRUE && export GOROOT=~/.local/lib/go' >> ~/.bashrc && source ~/.bashrc",
        "pip3 install numpy",
    ]
    for command in commands:
        run_command(command)

    if os.path.isdir("lattigo"):
        print("lattigo already exists")
    else:
        print("Installing lattigo")
        run_command("git clone https://github.com/hcholab/lattigo && cd lattigo && git switch lattigo_pca")

    if os.path.isdir("mpc-core"):
        print("mpc-core already exists")
    else:
        print("Installing mpc-core")
        run_command("git clone https://github.com/hhcho/mpc-core")

    if os.path.isdir("sfgwas"):
        print("sfgwas already exists")
    else:
        print("Installing sfgwas")
        run_command("git clone https://github.com/simonjmendelsohn/sfgwas && cd sfgwas")

    print("Finished installing dependencies")


def generate_shared_keys(role: int) -> None:
    doc_ref_dict: dict = get_doc_ref_dict()
    print("Generating shared keys...")

    private_key_path = os.path.join(constants.SFKIT_DIR, "my_private_key.txt")
    with open(private_key_path, "r") as f:
        my_private_key = PrivateKey(f.readline().rstrip().encode(), encoder=HexEncoder)

    for i, other_email in enumerate(doc_ref_dict["participants"]):
        if i == role:
            continue
        other_public_key_str: str = doc_ref_dict["personal_parameters"][other_email]["PUBLIC_KEY"]["value"]
        while not other_public_key_str:
            if other_email == "broad":
                print("Waiting for the Broad (CP0) to set up...")
            else:
                print(f"No public key found for {other_email}.  Waiting...")
            time.sleep(5)
            doc_ref_dict: dict = get_doc_ref_dict()
            other_public_key_str: str = doc_ref_dict["personal_parameters"][other_email]["PUBLIC_KEY"]["value"]
        other_public_key = PublicKey(other_public_key_str.encode(), encoder=HexEncoder)
        assert my_private_key != other_public_key, "Private and public keys must be different"
        shared_key = Box(my_private_key, other_public_key).shared_key()
        shared_key_path = os.path.join(constants.SFKIT_DIR, f"shared_key_{min(role, i)}_{max(role, i)}.bin")
        with open(shared_key_path, "wb") as f:
            f.write(shared_key)

    random.seed(doc_ref_dict["personal_parameters"]["Broad"]["PUBLIC_KEY"]["value"])
    global_shared_key = random.getrandbits(256).to_bytes(32, "big")
    with open(os.path.join(constants.SFKIT_DIR, "shared_key_global.bin"), "wb") as f:
        f.write(global_shared_key)

    print(f"Shared keys generated and saved to {constants.SFKIT_DIR}.")


def update_config_files(role: str, phase) -> None:
    doc_ref_dict: dict = get_doc_ref_dict()
    print("Begin updating config files")
    data_path_path: str = os.path.join(constants.SFKIT_DIR, "data_path.txt")
    geno_file_prefix, data_path = "", ""
    if role != "0":
        with open(data_path_path, "r") as f:
            geno_file_prefix = f.readline().rstrip()
            data_path = f.readline().rstrip()
    update_configParty(role, geno_file_prefix, data_path)
    update_configGlobal(doc_ref_dict, phase)


# def update_data_path_in_config_file_lungGCPFinal(role: str, data_path: str) -> None:
#     if role != "0":
#         config_file_path = f"sfgwas/config/configLocal.Party{role}.toml"
#         data = toml.load(config_file_path)
#         data["geno_binary_file_prefix"] = f"{data_path}/lung_split/geno_party{role}"
#         data["geno_block_size_file"] = f"{data_path}/lung_split/geno_party{role}.blockSizes.txt"
#         data["pheno_file"] = f"{data_path}/lung_split/pheno_party{role}.txt"
#         data["covar_file"] = f"{data_path}/lung_split/cov_party{role}.txt"
#         data["snp_position_file"] = f"{data_path}/lung/pos.txt"
#         with open(config_file_path, "w") as f:
#             toml.dump(data, f)


def update_configParty(role: str, geno_file_prefix, data_path: str) -> None:
    config_file_path = f"sfgwas/config/configLocal.Party{role}.toml"
    data = toml.load(config_file_path)

    if role != "0":
        data["geno_binary_file_prefix"] = f"{geno_file_prefix}"
        data["geno_block_size_file"] = f"{data_path}/chrom_sizes.txt"
        data["pheno_file"] = f"{data_path}/pheno.txt"
        data["covar_file"] = f"{data_path}/cov.txt"
        data["snp_position_file"] = f"{data_path}/snp_pos.txt"
        data["sample_keep_file"] = f"{data_path}/sample_keep.txt"
        data["snp_ids_file"] = f"{data_path}/snp_ids.txt"
        data["geno_count_file"] = f"{data_path}/all.gcount.transpose.bin"

    data["shared_keys_path"] = constants.SFKIT_DIR

    with open(config_file_path, "w") as f:
        toml.dump(data, f)


def update_configGlobal(doc_ref_dict: dict, phase) -> None:
    config_file_path = "sfgwas/config/configGlobal.toml"
    data = toml.load(config_file_path)

    print("Updating NUM_INDS and NUM_SNPS")
    for i, participant in enumerate(doc_ref_dict["participants"]):
        data["num_inds"][i] = int(doc_ref_dict["personal_parameters"][participant]["NUM_INDS"]["value"])
        print("NUM_INDS for", participant, "is", data["num_inds"][i])
        assert i == 0 or data["num_inds"][i] > 0, "NUM_INDS must be greater than 0"
    data["num_snps"] = int(doc_ref_dict["parameters"]["NUM_SNPS"]["value"])
    print("NUM_SNPS is", data["num_snps"])
    assert data["num_snps"] > 0, "NUM_SNPS must be greater than 0"

    data["phase"] = phase
    if phase == "2":
        data["use_cached_qc"] = True
    if phase == "3":
        data["use_cached_qc"] = True
        data["use_cached_pca"] = True

    # Update the ip addresses and ports
    for i, participant in enumerate(doc_ref_dict["participants"]):
        ip_addr = doc_ref_dict["personal_parameters"][participant]["IP_ADDRESS"]["value"]
        data["servers"][f"party{i}"]["ipaddr"] = ip_addr

    _, p1, p2 = doc_ref_dict["personal_parameters"][doc_ref_dict["participants"][0]]["PORTS"]["value"].split(",")
    data["servers"]["party0"]["ports"]["party1"] = p1
    data["servers"]["party0"]["ports"]["party2"] = p2

    _, _, p2 = doc_ref_dict["personal_parameters"][doc_ref_dict["participants"][1]]["PORTS"]["value"].split(",")
    data["servers"]["party1"]["ports"]["party2"] = p2

    with open(config_file_path, "w") as f:
        toml.dump(data, f)


def build_sfgwas() -> None:
    print("Building sfgwas code")
    command = """export PYTHONUNBUFFERED=TRUE && export GOROOT=~/.local/lib/go && cd sfgwas && go get -t github.com/simonjmendelsohn/sfgwas && go build"""
    run_command(command)
    print("Finished building sfgwas code")


def start_sfgwas(role: str) -> None:
    print("Begin SFGWAS protocol")
    protocol_command = f"export PID={role} && go run sfgwas.go | tee /dev/tty > stdout_party{role}.txt"
    command = f"export PYTHONUNBUFFERED=TRUE && export GOROOT=~/.local/lib/go && cd sfgwas && {protocol_command}"
    run_command(command)
    print("Finished SFGWAS protocol")
