from sfkit.auth.auth import auth
from sfkit.auth.setup_networking import setup_networking
from sfkit.encryption.mpc.encrypt_data import encrypt_data
from sfkit.encryption.generate_personal_keys import generate_personal_keys
from sfkit.parser import get_parser
from sfkit.protocol.register_data import register_data
from sfkit.protocol.run_protocol import run_protocol


def main() -> None:
    parser = get_parser()
    args = parser.parse_args()

    if args.command == "auth":
        study_title = args.study_title or ""
        auth(study_title)
    elif args.command == "networking":
        setup_networking()
    elif args.command == "generate_keys":
        generate_personal_keys()
    elif args.command == "encrypt_data":
        encrypt_data()
    elif args.command == "register_data":
        geno_binary_file_prefix = args.geno_binary_file_prefix or ""
        data_path = args.data_path or ""
        register_data(geno_binary_file_prefix, data_path)
    elif args.command == "run_protocol":
        phase: str = args.phase or ""
        demo: bool = args.demo or False
        run_protocol(phase, demo)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
