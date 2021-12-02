import sys

import nacl.secret
import nacl.utils
from nacl.encoding import HexEncoder
from nacl.public import Box, PrivateKey, PublicKey
from tqdm import tqdm

from random_number_generator import RandomNumberGenerator


def encrypt(file, rng, mode):
    """
    Encrypts the given file using the given random number generator in a manner
    that is compatible with the secret-sharing scheme used in our GWAS protocol.
    """
    input_file = open(f"input_data/{file}.txt", "r")
    output_file = open(f"output_data/{file}.bin", mode)
    file_lines = input_file.readlines()
    print(f"Encrypting input_data/{file}...")
    for line in tqdm(file_lines):
        line = line.strip()
        line = line.split("\t")
        for genotype in line:
            output_file.write((str(int(genotype) - rng.next()) + " ").encode("utf-8"))
        output_file.write(b"\n")


def get_shared_keys(my_private_key, other_public_key):
    """
    Given the private key of the user and the public key of the other user, generate 2 shared keys.
    The first is for the user with role 1 and the second is for the user with role 2.
    """
    shared_key_prototype = Box(my_private_key, other_public_key)
    if debug:
        print("Shared key prototype: ", shared_key_prototype.shared_key().hex())
    box = nacl.secret.SecretBox(shared_key_prototype.shared_key())
    nonce = 1
    message = b"bqvbiknychqjywxwjihfrfhgroxycxxj"  # some arbitrary 32 letter string
    if debug:
        print("nonce in hex: ", nonce.to_bytes(24, byteorder="big").hex())
        print("Byte message: ", message)
    shared_key_1 = box.encrypt(
        message, nonce=nonce.to_bytes(24, byteorder="big")
    ).ciphertext[16:]
    # python library has extra 16 bytes at beginning; see https://doc.libsodium.org/secret-key_cryptography/secretbox#notes
    nonce += 1
    if debug:
        print("nonce in hex: ", nonce.to_bytes(24, byteorder="big").hex())
    shared_key_2 = box.encrypt(
        message, nonce=nonce.to_bytes(24, byteorder="big")
    ).ciphertext[16:]

    if debug:
        print("Role 1's Key:", shared_key_1.hex())
        print("Role 2's Key:", shared_key_2.hex())

    return [None, shared_key_1, shared_key_2]


def get_users_input():
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


def main():
    (role, my_private_key, other_public_key) = get_users_input()

    shared_keys = get_shared_keys(my_private_key, other_public_key)

    rng1, rng2 = (
        RandomNumberGenerator(shared_keys[1]),
        RandomNumberGenerator(shared_keys[2]),
    )

    # encrypt the data
    files = ["cov", "pheno", "geno"]
    if role == 1:
        for file in files:
            encrypt(file, rng1, "wb")
    elif role == 2:
        for file in files:
            encrypt(file, rng2, "wb")

    print("\n\nThe encryption is complete. Please upload output_data to Google Cloud.")


if __name__ == "__main__":
    global debug
    debug = False
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        debug = True
    main()
