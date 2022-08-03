import os

import toml
from sfkit.protocol.utils import constants
from sfkit.protocol.utils.helper_functions import run_command


def run_sfgwas_protocol(doc_ref_dict: dict, role: str) -> None:
    print("\n\n Begin running SFGWAS protocol \n\n")
    install_sfgwas()
    update_config_files(doc_ref_dict, role)
    build_sfgwas()
    start_sfgwas()


def install_sfgwas() -> None:
    print("\n\n Begin installing dependencies \n\n")
    commands = """sudo apt-get update -y
                    sudo apt-get install python3-pip wget git -y
                    sudo wget https://golang.org/dl/go1.18.1.linux-amd64.tar.gz
                    sudo tar -C /usr/local -xzf go1.18.1.linux-amd64.tar.gz
                    sudo echo 'export PATH=$PATH:/usr/local/go/bin' >> .bashrc 
                    source .bashrc # cannot use sudo because source is a shell command, not an independent program
                    sudo pip3 install numpy"""
    for command in commands.split("\n"):
        run_command(command)

    if os.path.isdir("lattigo"):
        print("\n\n lattigo already exists \n\n")
    else:
        print("\n\n Installing lattigo \n\n")
        run_command("git clone https://github.com/hcholab/lattigo && cd lattigo && git switch lattigo_pca")

    if os.path.isdir("mpc-core"):
        print("\n\n mpc-core already exists \n\n")
    else:
        print("\n\n Installing mpc-core \n\n")
        run_command("git clone https://github.com/hhcho/mpc-core")

    if os.path.isdir("sfgwas-private"):
        print("\n\n sfgwas-private already exists \n\n")
    else:
        print("\n\n Installing sfgwas-private \n\n")
        run_command("git clone https://github.com/hhcho/sfgwas-private && cd sfgwas-private && git switch release")

    print("\n\n Finished installing dependencies \n\n")


def update_config_files(doc_ref_dict: dict, role: str) -> None:
    print("\n\n Begin updating config files \n\n")
    update_data_path_in_config_file(role)
    update_ip_addresses_and_ports_in_config_fille(doc_ref_dict)


def update_data_path_in_config_file(role: str) -> None:
    data_path_path = os.path.join(constants.sfkit_DIR, "data_path.txt")
    with open(data_path_path, "r") as f:
        data_path = f.readline().rstrip()
    config_file_path = f"sfgwas-private/config/lungGCPFinal/configLocal.Party{role}.toml"
    data = toml.load(config_file_path)
    data["geno_binary_file_prefix"] = f"{data_path}/lung_split/geno_party{role}"
    data["geno_block_size_file"] = f"{data_path}/lung_split/geno_party{role}.blockSizes.txt"
    data["pheno_file"] = f"{data_path}/lung_split/pheno_party{role}.txt"
    data["covar_file"] = f"{data_path}/lung_split/cov_party{role}.txt"
    data["snp_position_file"] = f"{data_path}/lung/pos.txt"
    with open(config_file_path, "w") as f:
        toml.dump(data, f)


def update_ip_addresses_and_ports_in_config_fille(doc_ref_dict):
    config_file_path = "sfgwas-private/config/lungGCPFinal/configGlobal.toml"
    data = toml.load(config_file_path)

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
    print("\n\n Building sfgwas code \n\n")
    command = """cd sfgwas-private && go get -t github.com/hhcho/sfgwas-private &&\
                go build &&\
                mkdir -p stdout"""
    run_command(command)
    print("\n\n Finished building sfgwas code \n\n")


# TODO: edit batch_run.sh to correspond to current role


def start_sfgwas() -> None:
    print("Begin SFGWAS protocol")
    command = "bash batch_run.sh"
    run_command(command)
    print("\n\n Finished SFGWAS protocol \n\n")
