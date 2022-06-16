import sys
from sftools.encryption_keys.encrypt_data import encrypt_data
from sftools.encryption_keys.generate_personal_keys import generate_personal_keys
from sftools.protocol.validate_data import main as validate_data
from sftools.protocol.run_protocol import main as run_protocol


def main():
    if len(sys.argv) < 2:
        print("Usage: sftools <generate_personal_keys | encrypt_data | validate_data | run_protocol>")
        exit(1)
    if sys.argv[1] == "generate_personal_keys":
        generate_personal_keys()
    elif sys.argv[1] == "encrypt_data":
        encrypt_data()
    elif sys.argv[1] == "validate_data":
        validate_data()
    elif sys.argv[1] == "run_protocol":
        run_protocol()


def hi():
    print("Hello World!")
