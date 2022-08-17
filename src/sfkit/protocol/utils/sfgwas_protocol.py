import fileinput
import os
import time

import toml
from google.cloud import firestore
from nacl.encoding import HexEncoder
from nacl.public import Box, PrivateKey, PublicKey
from sfkit.protocol.utils import constants
from sfkit.protocol.utils.helper_functions import run_command


def run_sfgwas_protocol(doc_ref, role: str) -> None:
    configuration = "lungPgen"

    print(f"Begin running SFGWAS protocol with {configuration} configuration.")
    install_sfgwas()

    generate_shared_keys(doc_ref, int(role))
    update_config_files(doc_ref, role, configuration)
    build_sfgwas(configuration)
    update_batch_run(role)
    start_sfgwas()


def install_sfgwas() -> None:
    print("Begin installing dependencies")
    commands = [
        "sudo apt-get update -y",
        "sudo apt-get install python3-pip wget git zip unzip -y",
        "sudo wget https://golang.org/dl/go1.18.1.linux-amd64.tar.gz",
        "sudo tar -C /usr/local -xzf go1.18.1.linux-amd64.tar.gz",
        "sudo wget https://s3.amazonaws.com/plink2-assets/alpha3/plink2_linux_avx2_20220603.zip",
        "sudo unzip -o plink2_linux_avx2_20220603.zip -d /usr/local",
        "sudo echo 'export PATH=$PATH:/usr/local/' >> .bashrc",
        "sudo echo 'export PATH=$PATH:/usr/local/go/bin' >> .bashrc",
        "source .bashrc # cannot use sudo because source is a shell command, not an independent program",
        "sudo pip3 install numpy",
    ]
    for command in commands:
        run_command(command)

    if os.path.isdir("lattigo"):
        print("lattigo already exists")
    else:
        print("Installing lattigo")
        run_command("git clone https://github.com/hcholab/lattigo && cd lattigo && git switch lattigo_pca")

    # need to get token since the repos are currently private
    doc_ref = firestore.Client().collection("meta").document("token")
    doc_ref_dict: dict = doc_ref.get().to_dict() or {}
    [(username, token)] = doc_ref_dict.items()

    if os.path.isdir("mpc-core"):
        print("mpc-core already exists")
    else:
        print("Installing mpc-core")
        run_command(f"git clone https://{username}:{token}@github.com/hhcho/mpc-core")

    if os.path.isdir("sfgwas-private"):
        print("sfgwas-private already exists")
    else:
        print("Installing sfgwas-private")
        run_command(
            f"git clone https://{username}:{token}@github.com/hhcho/sfgwas-private && cd sfgwas-private && git switch simon-shared-keys"  # TODO: git switch release
        )

    print("Finished installing dependencies")


def generate_shared_keys(doc_ref, role: int) -> None:
    doc_ref_dict: dict = doc_ref.get().to_dict() or {}
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
            doc_ref_dict: dict = doc_ref.get().to_dict() or {}
            other_public_key_str: str = doc_ref_dict["personal_parameters"][other_email]["PUBLIC_KEY"]["value"]
        other_public_key = PublicKey(other_public_key_str.encode(), encoder=HexEncoder)
        assert my_private_key != other_public_key, "Private and public keys must be different"
        shared_key = Box(my_private_key, other_public_key).shared_key()
        shared_key_path = os.path.join(constants.SFKIT_DIR, f"shared_key{min(role, i)}{max(role, i)}.txt")
        with open(shared_key_path, "wb") as f:
            f.write(shared_key)

    print(f"Shared keys generated and saved to {constants.SFKIT_DIR}.")


def update_config_files(doc_ref, role: str, configuration: str) -> None:
    doc_ref_dict: dict = doc_ref.get().to_dict() or {}
    print("Begin updating config files")
    data_path_path: str = os.path.join(constants.SFKIT_DIR, "data_path.txt")
    geno_file_prefix, data_path = "", ""
    if role != "0":
        with open(data_path_path, "r") as f:
            geno_file_prefix = f.readline().rstrip()
            data_path = f.readline().rstrip()
    if configuration == "lungGCPFinal":
        update_data_path_in_config_file_lungGCPFinal(role, data_path)
    elif configuration == "lungPgen":
        update_data_path_in_config_file_lungPgen(role, geno_file_prefix, data_path)
    else:
        raise ValueError(f"unknown configuration: {configuration}")
    update_configGlobal(doc_ref_dict, configuration)


def update_data_path_in_config_file_lungGCPFinal(role: str, data_path: str) -> None:
    if role != "0":
        config_file_path = f"sfgwas-private/config/lungGCPFinal/configLocal.Party{role}.toml"
        data = toml.load(config_file_path)
        data["geno_binary_file_prefix"] = f"{data_path}/lung_split/geno_party{role}"
        data["geno_block_size_file"] = f"{data_path}/lung_split/geno_party{role}.blockSizes.txt"
        data["pheno_file"] = f"{data_path}/lung_split/pheno_party{role}.txt"
        data["covar_file"] = f"{data_path}/lung_split/cov_party{role}.txt"
        data["snp_position_file"] = f"{data_path}/lung/pos.txt"
        with open(config_file_path, "w") as f:
            toml.dump(data, f)


def update_data_path_in_config_file_lungPgen(role: str, geno_file_prefix, data_path: str) -> None:
    config_file_path = f"sfgwas-private/config/lungPgen/configLocal.Party{role}.toml"
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


def update_configGlobal(doc_ref_dict: dict, configuration: str) -> None:
    config_file_path = f"sfgwas-private/config/{configuration}/configGlobal.toml"
    data = toml.load(config_file_path)

    # data["use_precomputed_geno_count"] = True
    # data["num_inds"] = [0, 4585, 4513]

    print("Checking NUM_INDS")
    for i, participant in enumerate(doc_ref_dict["participants"]):
        assert doc_ref_dict["personal_parameters"][participant]["NUM_INDS"]["value"] == str(data["num_inds"][i]), (
            f"NUM_INDS for {participant} is {doc_ref_dict['personal_parameters'][participant]['NUM_INDS']['value']}, "
            f"but should be {data['num_inds'][i]}"
        )

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


def build_sfgwas(configuration: str) -> None:
    # for line in fileinput.input(files="sfgwas-private/main_test.go", inplace=True):
    # if "var defaultConfigPath = " in line:
    #     print(f'var defaultConfigPath = "config/{configuration}"')
    # elif "func TestGwas(t *testing.T) {" in line:
    #     print("func TestGwasSimonDemo(t *testing.T) {")
    # else:
    #     print(line, end="")

    print("Building sfgwas code")
    run_command("pwd")
    command = """source .bashrc && cd sfgwas-private && go get -t github.com/hhcho/sfgwas-private && go build && mkdir -p stdout"""
    run_command(command)
    print("Finished building sfgwas code")


def update_batch_run(role: str) -> None:
    for line in fileinput.input(files="sfgwas-private/batch_run.sh", inplace=True):
        if "START=" in line:
            print(f"START={role}")
        elif "END=" in line:
            print(f"END={role}")
        # elif "TESTNAME=" in line:
        #     print("TESTNAME=TestGwasSimonDemo")
        else:
            print(line, end="")


def start_sfgwas() -> None:
    print("Begin SFGWAS protocol")
    command = "source .bashrc && cd sfgwas-private && bash batch_run.sh"
    run_command(command)
    print("Finished SFGWAS protocol")
