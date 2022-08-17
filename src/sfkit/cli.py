import argparse

from sfkit.auth.auth import auth
from sfkit.auth.setup_networking import setup_networking
from sfkit.encryption_keys.encrypt_data import encrypt_data
from sfkit.encryption_keys.generate_personal_keys import generate_personal_keys
from sfkit.protocol.register_data import register_data
from sfkit.protocol.run_protocol import run_protocol


def main():
    parser = argparse.ArgumentParser(description="Run workflow with sfkit.  Start with `sfkit auth` to authenticate.")
    subparsers = parser.add_subparsers(dest="command")
    authparser = subparsers.add_parser("auth", help="Authenticate with the CLI")
    authparser.add_argument("--sa_key", help="Path to the service account key file")
    authparser.add_argument("--study_title", help=argparse.SUPPRESS)
    subparsers.add_parser("networking", help="Setup the networking, including your IP address and any relevant ports")
    subparsers.add_parser("encrypt_data", help="Encrypt your MPC-GWAS data")
    generatekeysparser = subparsers.add_parser(
        "generate_keys",
        help="Generate your public and private cryptographic keys for use in encrypting the data",
    )
    generatekeysparser.add_argument("--study_title", help=argparse.SUPPRESS)
    registerdataparser = subparsers.add_parser(
        "register_data", help="Register and validate your data.", description="Register and validate your data."
    )
    registerdataparser.add_argument(
        "--geno_binary_file_prefix",
        help="Path to the genotype binary file prefix (e.g. 'for_sfgwas/lung/pgen_converted/party1/geno/lung_party1_chr%%d'",
    )  # two percent-signs to escape the first one
    registerdataparser.add_argument(
        "--data_path",
        help="Directory containing the data files (chrom_sizes.txt, pheno.txt, cov.txt, snp_pos.txt, sample_keep.txt, snp_ids.txt, all.gcount.transpose.bin)",
    )
    runprotocol = subparsers.add_parser(
        "run_protocol",
        help="Run the protocol. As this command may be long-running, it is recommended that you run it using nohup (`touch nohup.out; nohup sfkit run_protocol & tail -f nohup.out`) or a tool like screen or tmux",
    )
    runprotocol.add_argument("--study_title", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.command == "auth":
        sa_key = args.sa_key or ""
        study_title = args.study_title or ""
        auth(sa_key, study_title)
    elif args.command == "networking":
        setup_networking()
    elif args.command == "generate_keys":
        study_title: str = args.study_title or ""
        generate_personal_keys(study_title)
    elif args.command == "encrypt_data":
        encrypt_data()
    elif args.command == "register_data":
        geno_binary_file_prefix = args.geno_binary_file_prefix or ""
        data_path = args.data_path or ""
        register_data(geno_binary_file_prefix, data_path)
    elif args.command == "run_protocol":
        study_title: str = args.study_title or ""
        run_protocol(study_title)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
