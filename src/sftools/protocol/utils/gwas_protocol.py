import subprocess
import time


def run_gwas_protocol(doc_ref_dict: dict, role: str) -> None:
    print("\n\n Begin running GWAS protocol \n\n")
    install_gwas_dependencies()
    install_gwas_repo()
    install_ntl_library()
    compile_gwas_code()
    connect_to_other_vms(doc_ref_dict, role)
    copy_data_to_gwas_repo("./encrypted_data", role)
    start_datasharing(role)
    start_gwas(role)


def install_gwas_dependencies() -> None:
    print("\n\n Begin installing dependencies \n\n")
    commands = """sudo apt-get --assume-yes update 
                    sudo apt-get --assume-yes install build-essential 
                    sudo apt-get --assume-yes install clang-3.9 
                    sudo apt-get --assume-yes install libgmp3-dev 
                    sudo apt-get --assume-yes install libssl-dev 
                    sudo apt-get --assume-yes install libsodium-dev 
                    sudo apt-get --assume-yes install libomp-dev 
                    sudo apt-get --assume-yes install netcat 
                    sudo apt-get --assume-yes install git 
                    sudo apt-get --assume-yes install python3-pip 
                    sudo pip3 install numpy"""
    for command in commands.split("\n"):
        if subprocess.run(command, shell=True).returncode != 0:
            print(f"Failed to perform command {command}")
            exit(1)
    print("\n\n Finished installing dependencies \n\n")


def install_gwas_repo() -> None:
    print("\n\n Begin installing GWAS repo \n\n")
    subprocess.run("git clone https://github.com/simonjmendelsohn/secure-gwas secure-gwas", shell=True)
    print("\n\n Finished installing GWAS repo \n\n")


def install_ntl_library() -> None:
    print("\n\n Begin installing NTL library \n\n")
    commands = """curl https://libntl.org/ntl-10.3.0.tar.gz --output ntl-10.3.0.tar.gz
                tar -zxvf ntl-10.3.0.tar.gz
                cp secure-gwas/code/NTL_mod/ZZ.h ntl-10.3.0/include/NTL/
                cp secure-gwas/code/NTL_mod/ZZ.cpp ntl-10.3.0/src/
                cd ntl-10.3.0/src && ./configure NTL_THREAD_BOOST=on
                cd ntl-10.3.0/src && make all
                cd ntl-10.3.0/src && sudo make install"""
    for command in commands.split("\n"):
        if subprocess.run(command, shell=True).returncode != 0:
            print(f"Failed to perform command {command}")
            exit(1)
    print("\n\n Finished installing NTL library \n\n")


def compile_gwas_code() -> None:
    print("\n\n Begin compiling GWAS code \n\n")
    command = """cd secure-gwas/code && COMP=$(which clang++) &&\
                sed -i "s|^CPP.*$|CPP = ${COMP}|g" Makefile &&\
                sed -i "s|^INCPATHS.*$|INCPATHS = -I/usr/local/include|g" Makefile &&\
                sed -i "s|^LDPATH.*$|LDPATH = -L/usr/local/lib|g" Makefile &&\
                sudo make"""
    if subprocess.run(command, shell=True).returncode != 0:
        print(f"Failed to perform command {command}")
        exit(1)
    print("\n\n Finished compiling GWAS code \n\n")


def connect_to_other_vms(doc_ref_dict: dict, role: str) -> None:
    print("\n\n Begin connecting to other VMs \n\n")
    ip_addresses = [
        doc_ref_dict["personal_parameters"][user]["IP_ADDRESS"]["value"] for user in doc_ref_dict["participants"]
    ]
    print("IP addresses:", ip_addresses)
    ports = [
        doc_ref_dict["personal_parameters"][user]["PORTS"]["value"].split(",") for user in doc_ref_dict["participants"]
    ]
    # print("Ports:", ports)
    print("Using port 8055 for testing")
    if role == "1":
        # command = f"nc -k -l -p '{ports[1][2]}' &"
        command = "nc -k -l -p 8055 &"
        if subprocess.run(command, shell=True).returncode != 0:
            print(f"Failed to perform command {command}")
            exit(1)
        # command = f"nc -w 5 -v -z '{ip_addresses[0]}' '{ports[0][1]}'"
        command = f"nc -w 5 -v -z '{ip_addresses[0]}' '8055'"
        while subprocess.run(command, shell=True).returncode != 0:
            time.sleep(5)
    elif role == "2":
        # command = f"nc -w 5 -v -z '{ip_addresses[0]}' '{ports[0][2]}'"
        command = f"nc -w 5 -v -z '{ip_addresses[0]}' '8055'"
        while subprocess.run(command, shell=True).returncode != 0:
            time.sleep(5)
        # command = f"nc -w 5 -v -z '{ip_addresses[1]}' '{ports[1][2]}'"
        command = f"nc -w 5 -v -z '{ip_addresses[0]}' '8055'"
        while subprocess.run(command, shell=True).returncode != 0:
            time.sleep(5)
    else:
        raise ValueError("Invalid role")
    print("\n\n Finished connecting to other VMs \n\n")


def copy_data_to_gwas_repo(data_path: str, role: str) -> None:
    print("\n\n Copy data to GWAS repo \n\n")
    commands = f"""cp '{data_path}'/g.bin secure-gwas/test_data/g.bin 
    cp '{data_path}'/m.bin secure-gwas/test_data/m.bin 
    cp '{data_path}'/p.bin secure-gwas/test_data/p.bin 
    cp '{data_path}'/other_shared_key.bin secure-gwas/test_data/other_shared_key.bin 
    cp '{data_path}'/pos.txt secure-gwas/test_data/pos.txt 
    gsutil cp gs://secure-gwas-data/test.par.'{role}'.txt secure-gwas/par/test.par.'{role}'.txt"""
    for command in commands.split("\n"):
        if subprocess.run(command, shell=True).returncode != 0:
            print(f"Failed to perform command {command}")
            exit(1)
    print("\n\n Finished copying data to GWAS repo \n\n")


def start_datasharing(role: str) -> None:
    print("Sleeping before starting datasharing")
    time.sleep(30 * int(role))
    print("\n\n Begin starting data sharing \n\n")
    command = f"cd secure-gwas/code && bin/DataSharingClient '{role}' ../par/test.par.'{role}'.txt ../test_data/"
    if subprocess.run(command, shell=True).returncode != 0:
        print(f"Failed to perform command {command}")
        exit(1)
    print("\n\n Finished starting data sharing \n\n")


def start_gwas(role: str) -> None:
    print("Sleeping before starting GWAS")
    time.sleep(100 + 30 * int(role))
    print("\n\n Begin starting GWAS \n\n")
    command = f"cd secure-gwas/code && bin/GwasClient '{role}' ../par/test.par.'{role}'.txt"
    if subprocess.run(command, shell=True).returncode != 0:
        print(f"Failed to perform command {command}")
        exit(1)
    print("\n\n Finished GWAS \n\n")
