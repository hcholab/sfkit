import sys

from sftools.auth.auth import auth
from sftools.encryption_keys.encrypt_data import encrypt_data
from sftools.encryption_keys.generate_personal_keys import generate_personal_keys
from sftools.protocol.run_protocol import run_protocol
from sftools.protocol.validate_data import validate_data


def main():
    if len(sys.argv) < 2:
        print("Usage: sftools <auth | generate_personal_keys | encrypt_data | validate_data | run_protocol>")
        exit(1)
    if sys.argv[1] == "auth":
        auth()
    elif sys.argv[1] == "generate_personal_keys":
        generate_personal_keys()
    elif sys.argv[1] == "encrypt_data":
        encrypt_data()
    elif sys.argv[1] == "validate_data":
        validate_data()
    elif sys.argv[1] == "run_protocol":
        run_protocol()
    else:
        print("Usage: sftools <auth | generate_personal_keys | encrypt_data | validate_data | run_protocol>")
        exit(1)


if __name__ == "__main__":
    main()
