import sys

from sfkit.auth.auth import auth

# from sfkit.auth.set_study import set_study
from sfkit.auth.setup_networking import setup_networking
from sfkit.encryption_keys.encrypt_data import encrypt_data
from sfkit.encryption_keys.generate_personal_keys import generate_personal_keys
from sfkit.protocol.register_data import register_data
from sfkit.protocol.run_protocol import run_protocol


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: sfkit <auth | setup_networking | generate_personal_keys | register_data | encrypt_data | run_protocol>"
        )
        exit(1)
    if sys.argv[1] == "auth":
        auth()
    # elif sys.argv[1] == "set_study":
    #     set_study()
    elif sys.argv[1] == "setup_networking":
        setup_networking()
    elif sys.argv[1] == "generate_personal_keys":
        generate_personal_keys()
    elif sys.argv[1] == "register_data":
        register_data()
    elif sys.argv[1] == "encrypt_data":
        encrypt_data()
    elif sys.argv[1] == "run_protocol":
        run_protocol()
    else:
        print(
            "Usage: sfkit <auth | setup_networking | generate_personal_keys | register_data | encrypt_data | run_protocol>"
        )
        exit(1)


if __name__ == "__main__":
    main()
