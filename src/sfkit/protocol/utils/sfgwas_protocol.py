import fileinput
import os

import toml
from sfkit.protocol.utils import constants
from sfkit.protocol.utils.helper_functions import run_command


def run_sfgwas_protocol(doc_ref_dict: dict, role: str) -> None:
    configuration = "lungPgen"

    print(f"Begin running SFGWAS protocol with {configuration} configuration.")
    install_sfgwas()
    update_config_files(doc_ref_dict, role, configuration)
    build_sfgwas(configuration)
    update_batch_run(role)
    start_sfgwas()


def install_sfgwas() -> None:
    print("Begin installing dependencies")
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
        print("lattigo already exists")
    else:
        print("Installing lattigo")
        run_command("git clone https://github.com/hcholab/lattigo && cd lattigo && git switch lattigo_pca")

    if os.path.isdir("mpc-core"):
        print("mpc-core already exists")
    else:
        print("Installing mpc-core")
        run_command("git clone https://github.com/hhcho/mpc-core")

    if os.path.isdir("sfgwas-private"):
        print("sfgwas-private already exists")
    else:
        print("Installing sfgwas-private")
        run_command("git clone https://github.com/hhcho/sfgwas-private && cd sfgwas-private && git switch release")

    print("Finished installing dependencies")


def update_config_files(doc_ref_dict: dict, role: str, configuration: str) -> None:
    print("Begin updating config files")
    if role != "0":
        data_path_path = os.path.join(constants.sfkit_DIR, "data_path.txt")
        with open(data_path_path, "r") as f:
            data_path = f.readline().rstrip()
        if configuration == "lungGCPFinal":
            update_data_path_in_config_file_lungGCPFinal(role, data_path)
        elif configuration == "lungPgen":
            update_data_path_in_config_file_lungPgen(role, data_path)
        else:
            raise ValueError(f"unknown configuration: {configuration}")
    update_ip_addresses_and_ports_in_config_fille(doc_ref_dict, configuration)


def update_data_path_in_config_file_lungGCPFinal(role: str, data_path: str) -> None:
    config_file_path = f"sfgwas-private/config/lungGCPFinal/configLocal.Party{role}.toml"
    data = toml.load(config_file_path)
    data["geno_binary_file_prefix"] = f"{data_path}/lung_split/geno_party{role}"
    data["geno_block_size_file"] = f"{data_path}/lung_split/geno_party{role}.blockSizes.txt"
    data["pheno_file"] = f"{data_path}/lung_split/pheno_party{role}.txt"
    data["covar_file"] = f"{data_path}/lung_split/cov_party{role}.txt"
    data["snp_position_file"] = f"{data_path}/lung/pos.txt"
    with open(config_file_path, "w") as f:
        toml.dump(data, f)


def update_data_path_in_config_file_lungPgen(role: str, data_path: str) -> None:
    config_file_path = f"sfgwas-private/config/lungPgen/configLocal.Party{role}.toml"
    data = toml.load(config_file_path)
    data["geno_binary_file_prefix"] = f"{data_path}/lung/pgen_converted/party{role}/geno/lung_party{role}_chr%d"
    data["geno_block_size_file"] = f"{data_path}/lung/pgen_converted/party{role}/chrom_sizes.txt"
    data["pheno_file"] = f"{data_path}/lung/pgen_converted/party{role}/pheno_party{role}.txt"
    data["covar_file"] = f"{data_path}/lung/pgen_converted/party{role}/cov_party{role}.txt"
    data["snp_position_file"] = f"{data_path}/lung/pgen_converted/party{role}/snp_pos.txt"
    data["sample_keep_file"] = f"{data_path}/lung/pgen_converted/party{role}/sample_keep.txt"
    data["snp_ids_file"] = f"{data_path}/lung/pgen_converted/party{role}/snp_ids.txt"
    data["geno_count_file"] = f"{data_path}/lung/pgen_converted/party{role}/all.gcount.transpose.bin"
    with open(config_file_path, "w") as f:
        toml.dump(data, f)


def update_ip_addresses_and_ports_in_config_fille(doc_ref_dict: dict, configuration: str) -> None:
    config_file_path = f"sfgwas-private/config/{configuration}/configGlobal.toml"
    data = toml.load(config_file_path)

    data["use_precomputed_geno_count"] = True
    data["num_inds"] = [0, 4585, 4513]

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
    # update main_test.go TODO: should be already done
    for line in fileinput.input(files="sfgwas-private/main_test.go", inplace=True):
        if "var defaultConfigPath = " in line:
            print(f'var defaultConfigPath = "config/{configuration}"')
        else:
            print(line, end="")

    print("Building sfgwas code")
    command = """cd sfgwas-private && go get -t github.com/hhcho/sfgwas-private &&\
                go build &&\
                mkdir -p stdout"""
    run_command(command)
    print("Finished building sfgwas code")


def update_batch_run(role: str) -> None:
    for line in fileinput.input(files="sfgwas-private/batch_run.sh", inplace=True):
        if "START=" in line:
            print(f"START={role}")
        elif "END=" in line:
            print(f"END={role}")
        elif "TESTNAME=" in line:
            print("TESTNAME=TestGwas")
        else:
            print(line, end="")


def start_sfgwas() -> None:
    print("Begin SFGWAS protocol")
    command = "cd sfgwas-private && bash batch_run.sh"
    run_command(command)
    print("Finished SFGWAS protocol")
