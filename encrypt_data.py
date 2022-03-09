import os
import shutil
import sys

import nacl.secret
import nacl.utils
from nacl.encoding import HexEncoder
from nacl.public import Box, PrivateKey, PublicKey
from tqdm import tqdm

from random_number_generator import PseudoRandomNumberGenerator

BASE_P = 1461501637330902918203684832716283019655932542929


def encrypt_GMP(
    prng, input_dir, output_dir="encrypted_data"
):  # sourcery skip: ensure-file-closed, switch
    """
    Converts the data to GMP vectors (genotype, missing data, phenotype), encrypts
    them, and writes them to files.
    """
    geno_file = open(f"{input_dir}/geno.txt", "r")
    pheno_file = open(f"{input_dir}/pheno.txt", "r")
    cov_file = open(f"{input_dir}/cov.txt", "r")

    g_file = open(f"{output_dir}/g.bin", "wb")
    m_file = open(f"{output_dir}/m.bin", "wb")
    p_file = open(f"{output_dir}/p.bin", "wb")

    num_lines = sum(1 for _ in open(f"{input_dir}/pheno.txt", "r"))
    for _ in tqdm(range(num_lines)):
        p = (
            pheno_file.readline().rstrip().split()
            + cov_file.readline().rstrip().split()
        )
        p = [str((int(x) - prng.next()) % BASE_P) for x in p]

        geno_line = geno_file.readline().rstrip().split()
        g = [[-prng.next() % BASE_P for _ in range(len(geno_line))] for _ in range(3)]
        m = [-prng.next() % BASE_P for _ in range(len(geno_line))]
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
        print(
            "Shared key prototype: ",
            shared_key_prototype.shared_key().hex(),  # type: ignore
        )
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


def main():
    pk_files = [
        filename for filename in os.listdir(".") if filename.startswith("public_key_")
    ]
    assert (
        len(pk_files) == 1
    ), "Expected 1 file of the form 'public_key_*', found {}".format(len(pk_files))

    with open(pk_files[0], "r") as f:
        other_public_key = PublicKey(f.readline().rstrip(), encoder=HexEncoder)  # type: ignore
        other_role = f.readline().rstrip()
    role = 3 - int(other_role)

    with open("my_private_key.txt", "r") as f:
        my_private_key = PrivateKey(f.readline().rstrip(), encoder=HexEncoder)  # type: ignore
    assert (
        my_private_key != other_public_key
    ), "Private and public keys must be different"

    shared_keys = get_shared_keys(my_private_key, other_public_key)

    input_dir = input(
        "Enter the path to your input directory (the directory with cov.txt, geno.txt, pheno.txt, and pos.txt): "
    )
    encrypt_GMP(PseudoRandomNumberGenerator(shared_keys[role]), input_dir)

    with open("encrypted_data/other_shared_key.bin", "wb") as f:
        f.write(shared_keys[3 - role])
    shutil.copyfile(f"{input_dir}/pos.txt", "encrypted_data/pos.txt")

    print(
        "\n\nThe encryption is complete. Please upload everything in the encrypted_data directory to Google Cloud."
    )


if __name__ == "__main__":
    global debug
    debug = len(sys.argv) > 1 and sys.argv[1] == "debug"
    main()
