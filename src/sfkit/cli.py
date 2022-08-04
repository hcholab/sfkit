import argparse

from sfkit.auth.auth import auth
from sfkit.auth.setup_networking import setup_networking
from sfkit.encryption_keys.encrypt_data import encrypt_data
from sfkit.encryption_keys.generate_personal_keys import generate_personal_keys
from sfkit.protocol.register_data import register_data
from sfkit.protocol.run_protocol import run_protocol


def main():
    parser = argparse.ArgumentParser(description="Run workflow with sfkit")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("auth", help="Authenticate with the CLI")
    subparsers.add_parser(
        "setup_networking", help="Setup the networking, including your IP address and any relevant ports"
    )
    subparsers.add_parser("encrypt_data", help="Encrypt your data")
    subparsers.add_parser(
        "generate_personal_keys",
        help="Generate your public and private cryptographic keys for use in encrypting the data",
    )
    subparsers.add_parser("register_data", help="Register and validate your data.")
    runprotocol = subparsers.add_parser(
        "run_protocol",
        help="Run the protocol. As this command may be long-running, it is recommended that you run it using nohup. This will prevent it from terminating if you close this window/terminal. For example, `nohup sfkit run_protocol & tail -f nohup.out`. You can also use a tool like screen or tmux",
    )
    runprotocol.add_argument("--study_title", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.command == "auth":
        auth()
    elif args.command == "setup_networking":
        setup_networking()
    elif args.command == "generate_personal_keys":
        generate_personal_keys()
    elif args.command == "encrypt_data":
        encrypt_data()
    elif args.command == "register_data":
        register_data()
    elif args.command == "run_protocol":
        if args.study_title:
            run_protocol(study_title=args.study_title)
        else:
            run_protocol()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
