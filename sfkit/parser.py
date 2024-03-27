import argparse


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run workflow with sfkit.  Start with ``sfkit auth`` to authenticate."
    )
    subparsers = parser.add_subparsers(dest="command")
    auth = subparsers.add_parser("auth", help="Authenticate with the CLI")
    auth.add_argument(
        "--study_id",
        help="Study ID to authenticate with (for usage on Terra).  If not provided, you will be prompted to select from a list of available studies.",
    )
    networking = subparsers.add_parser(
        "networking", help="Set up the networking, including your IP address and any relevant ports"
    )
    networking.add_argument(
        "--ports",
        help="Comma-separated list of ports you want to use for communication for each other User respectively. In a two-party study, you only need to provide one port (e.g. 8100). For each port provided, you should be sure to open that port and the next few ports (for faster communication) in your firewall. If not provided, you may be prompted to enter a port for each participant.",
    )
    networking.add_argument(
        "--ip_address",
        help="IP address you want to use for communication.  If not provided, your external IP address will be determined automatically.",
    )
    subparsers.add_parser("generate_keys", help="Generate your public and private cryptographic keys")
    registerdataparser = subparsers.add_parser(
        "register_data", help="Register and validate your data.", description="Register and validate your data."
    )
    registerdataparser.add_argument(
        "--geno_binary_file_prefix",
        help="Absolute path to the genotype binary file prefix for SF-GWAS (e.g. ``/home/username/for_sfgwas/geno/ch%d``).  See https://sfkit.org/instructions#data_preparation for more details on the files you need.",
    )
    registerdataparser.add_argument(
        "--data_path",
        help="Absolute path to the data directory (files like ``pheno.txt`` and ``cov.txt`` for GWAS and ``data.txt`` for PCA) (e.g. ``/home/username/for_sfgwas``). See https://sfkit.org/instructions#data_preparation for more details on the files you need.",
    )
    runprotocol = subparsers.add_parser(
        "run_protocol",
        help="Run the protocol. When not using docker, this command will also install required dependencies and software updates as needed. As this command may be long-running, you may consider using ``nohup``, ``screen``, or ``tmux``.",
    )
    # runprotocol.add_argument(
    #     "--phase",
    #     help="Phase of the protocol to run (e.g. '1' for QC, 2 for PCA, 3 for Association Statistics)",
    # )
    runprotocol.add_argument("--skip_cp0", help="Skip the creation of cp0 for party 1", action="store_true")
    runprotocol.add_argument("--demo", help="Run the demo protocol", action="store_true")
    runprotocol.add_argument(
        "--visualize_results", help="Visualize the results in the UI (``Yes`` or ``No``) (default is ``No``)"
    )
    runprotocol.add_argument(
        "--results_path",
        help="The path in a GCP bucket (you have access to) where you would like to send the results of the protocol (e.g. ``<bucket>/<path>``).",
    )
    runprotocol.add_argument("--retry", help="Retry the protocol", action="store_true")

    subparsers.add_parser("server", help="Start the sfkit server.")
    client = subparsers.add_parser("client", help="Start the sfkit client.")
    client.add_argument("--study_id", help="Study ID for the client to use.")
    client.add_argument("--data_path", help="Path to the data directory for the client.")

    run_all = subparsers.add_parser("all", help="Run all commands.")
    run_all.add_argument("--study_id", help="Study ID for the client to use.")
    run_all.add_argument("--data_path", help="Path to the data directory for the client.")

    return parser
