import os

import toml
from sftools.protocol.utils import constants
from sftools.protocol.utils.helper_functions import run_shell_command


def run_sfgwas_protocol(doc_ref_dict: dict, role: str) -> None:
    print("\n\n Begin running SFGWAS protocol \n\n")
    install_sfgwas_dependencies()
    update_config_files(doc_ref_dict, role)
    build_sfgwas()
    start_sfgwas()


def install_sfgwas_dependencies() -> None:
    print("\n\n Begin installing dependencies \n\n")
    commands = """sudo apt-get update -y
                    sudo apt-get install python3-pip wget git -y
                    sudo wget https://golang.org/dl/go1.18.1.linux-amd64.tar.gz
                    sudo tar -C /usr/local -xzf go1.18.1.linux-amd64.tar.gz
                    sudo echo 'export PATH=$PATH:/usr/local/go/bin' >> .bashrc 
                    source .bashrc # cannot use sudo because source is a shell command, not an independent program
                    sudo pip3 install numpy 
                    git clone https://github.com/hcholab/lattigo
                    cd lattigo && git switch lattigo_pca
                    git clone https://simonjmendelsohn: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@github.com/hhcho/mpc-core
                    git clone https://simonjmendelsohn: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@github.com/hhcho/sfgwas-private
                    cd sfgwas-private && git switch release"""
    for command in commands.split("\n"):
        run_shell_command(command)
    print("\n\n Finished installing dependencies \n\n")


def update_config_files(doc_ref_dict: dict, role: str) -> None:
    data_path_path = os.path.join(constants.SFTOOLS_DIR, "data_path.txt")
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

    config_file_path = "sfgwas-private/config/lungGCPFinal/configGlobal.toml"
    data = toml.load(config_file_path)

    ip_addr = doc_ref_dict["personal_parameters"][doc_ref_dict["participants"][0]]["IP_ADDRESS"]["value"]
    data["servers"]["party0"]["ipaddr"] = ip_addr

    _, p1, p2 = doc_ref_dict["personal_parameters"][doc_ref_dict["participants"][0]]["PORTS"]["value"].split(",")
    data["servers"]["party0"]["ports"] = '{party1 = "' + p1 + '", party2 = "' + p2 + '"}'

    ip_addr = doc_ref_dict["personal_parameters"][doc_ref_dict["participants"][1]]["IP_ADDRESS"]["value"]
    data["servers"]["party1"]["ipaddr"] = ip_addr

    _, _, p2 = doc_ref_dict["personal_parameters"][doc_ref_dict["participants"][1]]["PORTS"]["value"].split(",")
    data["servers"]["party1"]["ports"] = '{party2 = "' + p2 + '"}'

    if len(doc_ref_dict["participants"]) > 2:
        ip_addr = doc_ref_dict["personal_parameters"][doc_ref_dict["participants"][2]]["IP_ADDRESS"]["value"]
        data["servers"]["party2"]["ipaddr"] = ip_addr

    with open(config_file_path, "w") as f:
        toml.dump(data, f)


def build_sfgwas() -> None:
    print("\n\n Building sfgwas code \n\n")
    command = """cd sfgwas-private && go get -t github.com/hhcho/sfgwas-private &&\
                go build &&\
                mkdir stdout"""
    run_shell_command(command)
    print("\n\n Finished building sfgwas code \n\n")


def start_sfgwas() -> None:
    print("Begin SFGWAS protocol")
    command = "bash batch_run.sh"
    run_shell_command(command)
    print("\n\n Finished SFGWAS protocol \n\n")
