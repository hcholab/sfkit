import argparse


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run workflow with sfkit.  Start with `sfkit auth` to authenticate.")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("auth", help="Authenticate with the CLI")
    networking = subparsers.add_parser(
        "networking", help="Setup the networking, including your IP address and any relevant ports"
    )
    networking.add_argument(
        "--ports",
        help="Comma-separated list of ports to use for communication.  If not provided, you will be prompted to enter them.",
    )
    networking.add_argument(
        "--ip_address",
        help="ip address you want to use for communication.  If not provided, your external ip address will be determined automatically.",
    )
    subparsers.add_parser("generate_keys", help="Generate your public and private cryptographic keys")
    registerdataparser = subparsers.add_parser(
        "register_data", help="Register and validate your data.", description="Register and validate your data."
    )
    registerdataparser.add_argument(
        "--geno_binary_file_prefix",
        help="Path to the genotype binary file prefix (e.g. '/home/username/for_sfgwas/geno/ch%d')",
    )  # two percent-signs to escape the first one
    registerdataparser.add_argument(
        "--data_path",
        help="Directory containing the data files (chrom_sizes.txt, pheno.txt, cov.txt, snp_pos.txt, sample_keep.txt, snp_ids.txt, all.gcount.transpose.bin) (e.g. /home/username/for_sfgwas)",
    )
    runprotocol = subparsers.add_parser(
        "run_protocol",
        help="Run the protocol. When not using docker, this command will also install required dependencies and software updates as needed. As this command may be long-running, you may want to run it using nohup or screen or tmux",
    )
    runprotocol.add_argument(
        "--phase", help="Phase of the protocol to run (e.g. '1' for QC, 2 for PCA, 3 for Association Statistics)"
    )
    runprotocol.add_argument("--demo", help="Run the demo protocol", action="store_true")
    runprotocol.add_argument("--visualize_results", help="Visualize the results in the UI (Yes or No)")
    runprotocol.add_argument(
        "--results_path",
        help="The path in a GCP bucket (you have access to) where you would like to send the results of the protocol.",
    )
    runprotocol.add_argument("--retry", help="Retry the protocol", action="store_true")

    return parser
