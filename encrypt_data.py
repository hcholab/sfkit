import sys

import nacl.secret
import nacl.utils
from nacl.encoding import HexEncoder
from nacl.public import Box, PrivateKey, PublicKey
from tqdm import tqdm

from random_number_generator import RandomNumberGenerator


def upload_others_shared_key(shared_keys, role):
    """
    upload the shared key of the other user to other_shared_key.txt
    """
    key = shared_keys[2] if role == 1 else shared_keys[1]
    with open("output_data/other_shared_key.txt", "w") as f:
        f.write(key.hex())


def encrypt(file, rng):
    """
    Encrypts the given file using the given random number generator in a manner
    that is compatible with the secret-sharing scheme used in our GWAS protocol.
    """
    input_file = open(f"input_data/{file}", "r")
    output_file = open(f"output_data/{file}", "w")
    file_lines = input_file.readlines()
    print(f"Encrypting input_data/{file}...")
    for line in tqdm(file_lines):
        line = line.strip()
        line = line.split("\t")
        for genotype in line:
            output_file.write(str(int(genotype) - rng.next()) + " ")
        output_file.write("\n")


def get_shared_keys(debug, my_private_key, other_public_key):
    """
    Given the private key of the user and the public key of the other user, generate 2 shared keys.
    The first is for the user with role 1 and the second is for the user with role 2.
    """
    shared_key_prototype = Box(my_private_key, other_public_key)
    box = nacl.secret.SecretBox(shared_key_prototype.shared_key())
    nonce = 1
    nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
    shared_key_1 = box.encrypt(
        b"Hello to you !!!", nonce=nonce.to_bytes(24, byteorder="big")
    ).ciphertext
    nonce += 1
    shared_key_2 = box.encrypt(
        b"Hello to you !!!", nonce=nonce.to_bytes(24, byteorder="big")
    ).ciphertext

    if debug:
        print("Role 1's Key:", shared_key_1)
        print("Role 2's Key:", shared_key_2)

    return [None, shared_key_1, shared_key_2]


def get_users_role_and_keys(debug):
    if debug:
        role = 1
        my_private_key = PrivateKey(
            "134197d25ddd95dda789fddbbd9f3329bab3ed5fe31a3b184cf40d780dd206e7",
            encoder=HexEncoder,
        )
        other_public_key = PublicKey(
            "b6abeabb695a23e76315ded61f9ba750f57c79b6eaa4ab0fc28ade4df8517a06",
            encoder=HexEncoder,
        )
    else:
        # get user's role
        role = int(input("Please enter your role (1 or 2): "))
        if role not in [1, 2]:
            print("Invalid role; role must be 1 or 2.  Exiting.")
            sys.exit(1)
        # read in the keys
        my_private_key = PrivateKey(
            input("Enter your private key: "), encoder=HexEncoder
        )
        other_public_key = PublicKey(
            input("Enter the other participant's public key: "), encoder=HexEncoder
        )

    return (role, my_private_key, other_public_key)


def main(debug=False):
    (role, my_private_key, other_public_key) = get_users_role_and_keys(debug)

    shared_keys = get_shared_keys(debug, my_private_key, other_public_key)

    rng = RandomNumberGenerator(shared_keys[role])

    files = ["cov.txt", "pheno.txt", "geno.txt"]
    for file in files:
        encrypt(file, rng)

    upload_others_shared_key(shared_keys, role)

    print("\n\nThe encryption is complete. Please upload output_data to Google Cloud.")


if __name__ == "__main__":
    debug = False
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        debug = True
    main(debug=debug)
