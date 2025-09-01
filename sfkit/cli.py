from sfkit.auth.auth import auth
from sfkit.auth.setup_networking import setup_networking
from sfkit.encryption.generate_personal_keys import generate_personal_keys
from sfkit.parser import get_parser
from sfkit.protocol.register_data import register_data
from sfkit.protocol.run_protocol import run_protocol
from sfkit.sidecar.client import client_command
from sfkit.sidecar.server import server_command
from sfkit.utils import constants


def main() -> None:
    parser = get_parser()
    args = vars(parser.parse_args())

    if args["command"] not in (None, "client"):
        print(f"SFKIT_API_URL: {constants.SFKIT_API_URL}")

    match args["command"]:
        case "server":
            server_command()
        case "client":
            client_command(**args)
        case "auth":
            auth(**args)
        case "networking":
            setup_networking(**args)
        case "generate_keys":
            generate_personal_keys()
        case "register_data":
            register_data(**args)
        case "run_protocol":
            run_protocol(**args)
        case "run" | "all":
            auth(**args)
            setup_networking()
            generate_personal_keys()
            register_data(**args)
            run_protocol(**args)
        case _:
            parser.print_help()
