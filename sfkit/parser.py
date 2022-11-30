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
    subparsers.add_parser("generate_keys", help="Generate your public and private cryptographic keys")
    registerdataparser = subparsers.add_parser(
        "register_data", help="Register and validate your data.", description="Register and validate your data."
    )
    registerdataparser.add_argument(
        "--geno_binary_file_prefix",
        help="Path to the genotype binary file prefix (e.g. 'for_sfgwas/lung/pgen_converted/party1/geno/lung_party1_chr%%d')",
    )  # two percent-signs to escape the first one
    registerdataparser.add_argument(
        "--data_path",
        help="Directory containing the data files (chrom_sizes.txt, pheno.txt, cov.txt, snp_pos.txt, sample_keep.txt, snp_ids.txt, all.gcount.transpose.bin)",
    )
    runprotocol = subparsers.add_parser(
        "run_protocol",
        help="Run the protocol. As this command may be long-running, you may want to run it using nohup or screen or tmux",
    )
    runprotocol.add_argument(
        "--phase", help="Phase of the protocol to run (e.g. '1' for QC, 2 for PCA, 3 for Association Statistics)"
    )
    runprotocol.add_argument("--demo", help="Run the demo protocol", action="store_true")

    return parser
