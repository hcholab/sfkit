import sys

from sftools.auth.auth import auth

# from sftools.auth.set_study import set_study
from sftools.auth.setup_networking import setup_networking
from sftools.encryption_keys.encrypt_data import encrypt_data
from sftools.encryption_keys.generate_personal_keys import generate_personal_keys
from sftools.protocol.register_data import register_data
from sftools.protocol.run_protocol import run_protocol


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: sftools <auth | setup_networking | generate_personal_keys | register_data | encrypt_data | run_protocol>"
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
            "Usage: sftools <auth | setup_networking | generate_personal_keys | register_data | encrypt_data | run_protocol>"
        )
        exit(1)


if __name__ == "__main__":
    main()
