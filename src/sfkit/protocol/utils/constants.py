import os

WEBSITE_URL = "https://secure-gwas-website-bhj5a4wkqa-uc.a.run.app"
METADATA_VM_IDENTITY_URL = (
    "http://metadata.google.internal/computeMetadata/v1/"
    "instance/service-accounts/default/identity?"
    "audience={}&format={}&licenses={}"
)
SERVER_GCP_PROJECT = "broad-cho-priv1"
SERVER_REGION = "us-central1"
SERVER_ZONE = f"{SERVER_REGION}-a"
NETWORK_NAME = "secure-gwas"
SUBNET_NAME = f"{NETWORK_NAME}-subnet"
INSTANCE_NAME_ROOT = NETWORK_NAME
PARAMETER_BUCKET = f"{NETWORK_NAME}-data"
TEMP_FOLDER = "src/temp"
PARAMETER_FILES = ["test.par.0.txt", "test.par.1.txt", "test.par.2.txt"]
# BASE_P = "1461501637330902918203684832716283019655932542929"
# DATA_VALIDATION_CONSTANT = 4 * len(BASE_P)
GWAS_RAW_INPUT_FILES = ["cov.txt", "geno.txt", "pheno.txt", "pos.txt"]
SFGWAS_INPUT_FILES = ["geno_party", "pheno_party", "cov_party", "pos.txt"]
SFGWAS_PGEN_INPUT_FILES = [
    "chrom_sizes.txt",
    "pheno",
    "cov",
    "snp_pos.txt",
    "snp_ids.txt",
    "all.gcount.transpose.bin",
]
NEEDED_INPUT_FILES = {
    "GWAS": GWAS_RAW_INPUT_FILES,
    "SFGWAS": SFGWAS_INPUT_FILES,
    "SFGWAS_pgen": SFGWAS_PGEN_INPUT_FILES,
}
SFKIT_DIR = os.path.expanduser("~/.config/sfkit")
AUTH_FILE = os.path.join(SFKIT_DIR, "auth.txt")

BROAD_VM_SOURCE_IP_RANGES = [
    "69.173.112.0/21",
    "69.173.127.232/29",
    "69.173.127.128/26",
    "69.173.127.0/25",
    "69.173.127.240/28",
    "69.173.127.224/30",
    "69.173.127.230/31",
    "69.173.120.0/22",
    "69.173.127.228/32",
    "69.173.126.0/24",
    "69.173.96.0/20",
    "69.173.64.0/19",
    "69.173.127.192/27",
    "69.173.124.0/23",
    "10.0.0.10",  # other VMs doing the computation
    "10.0.1.10",
    "10.0.2.10",
    "35.235.240.0/20",  # IAP TCP forwarding
]
