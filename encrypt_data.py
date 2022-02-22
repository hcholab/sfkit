import shutil
import sys

import nacl.secret
import nacl.utils
from nacl.encoding import HexEncoder
from nacl.public import Box, PrivateKey, PublicKey
from tqdm import tqdm

from random_number_generator import RandomNumberGenerator

BASE_P = 1461501637330902918203684832716283019655932542929

# deprecated by encrypt_GMP
# def encrypt(file, rng, mode):
#     """
#     Encrypts the given file using the given random number generator in a manner
#     that is compatible with the secret-sharing scheme used in our GWAS protocol.
#     """
#     input_file = open(f"input_data/{file}.txt", "r")
#     output_file = open(f"output_data/{file}.bin", mode)
#     file_lines = input_file.readlines()
#     print(f"Encrypting input_data/{file}...")
#     for line in tqdm(file_lines):
#         line = line.strip()
#         line = line.split("\t")
#         for genotype in line:
#             output_file.write((str(int(genotype) - rng.next()) + " ").encode("utf-8"))
#         output_file.write(b"\n")


def encrypt_GMP(rng, role):
    """
    Converts the data to GMP vectors (genotype, missing data, phenotype), encrypts
    them, and writes them to files.
    """
    geno_file = open("input_data/geno.txt", "r")
    pheno_file = open("input_data/pheno.txt", "r")
    cov_file = open("input_data/cov.txt", "r")

    g_file = open("output_data/g.bin", "wb")
    m_file = open("output_data/m.bin", "wb")
    p_file = open("output_data/p.bin", "wb")

    num_lines = sum(1 for _ in open("input_data/pheno.txt", "r"))
    for _ in tqdm(range(num_lines)):
        p = (
            pheno_file.readline().rstrip().split()
            + cov_file.readline().rstrip().split()
        )
        p = [str((int(x) - rng.next()) % BASE_P) for x in p]

        geno_line = geno_file.readline().rstrip().split()
        g = [[-rng.next() % BASE_P for _ in range(len(geno_line))] for _ in range(3)]
        m = [-rng.next() % BASE_P for _ in range(len(geno_line))]
        for j, val in enumerate(geno_line):
            if val == "0":
                g[0][j] = (g[0][j] + 1) % BASE_P
            elif val == "1":
                g[1][j] = (g[1][j] + 1) % BASE_P
            elif val == "2":
                g[2][j] = (g[2][j] + 1) % BASE_P
            else:
                m[j] = (m[j] + 1) % BASE_P

        g_text = (
            " ".join(map(str, g[0]))
            + " "
            + " ".join(map(str, g[1]))
            + " "
            + " ".join(map(str, g[2]))
            + "\n"
        )
        g_file.write(g_text.encode("utf-8"))
        m_file.write((" ".join([str(x) for x in m]) + "\n").encode("utf-8"))
        p_file.write((" ".join(p) + "\n").encode("utf-8"))

    geno_file.close()
    pheno_file.close()
    cov_file.close()

    g_file.close()
    m_file.close()
    p_file.close()


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
        role = int(
            input(
                "Please enter your role (1 or 2).  If you unsure your role, please check the study page on the website: "
            )
        )
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

    # convert to GMP and encrypt the data
    encrypt_GMP(RandomNumberGenerator(shared_keys[role]), role=role)

    with open("output_data/other_shared_key.bin", "wb") as f:
        f.write(shared_keys[3 - role])

    shutil.copyfile("input_data/pos.txt", "output_data/pos.txt")

    print("\n\nThe encryption is complete. Please upload output_data to Google Cloud.")


if __name__ == "__main__":
    global debug
    debug = len(sys.argv) > 1 and sys.argv[1] == "debug"
    main()
