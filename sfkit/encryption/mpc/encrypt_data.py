# for MPC-GWAS

import os
import shutil
import sys
import time

import checksumdir
import nacl.secret
import nacl.utils
from nacl.encoding import HexEncoder
from nacl.public import Box, PrivateKey, PublicKey

from sfkit.api import get_doc_ref_dict, get_username
from sfkit.encryption.mpc.random_number_generator import PseudoRandomNumberGenerator
from sfkit.utils import constants
from sfkit.utils.helper_functions import condition_or_fail

# from tqdm import tqdm


def encrypt_GMP(prng: PseudoRandomNumberGenerator, input_dir: str, output_dir: str) -> None:
    # sourcery skip: avoid-global-variables, avoid-single-character-names-variables, ensure-file-closed, require-parameter-annotation, snake-case-functions, switch
    """
    Converts the data to GMP vectors (genotype, missing data, phenotype), encrypts
    them, and writes them to files.
    """
    geno_file = open(f"{input_dir}/geno.txt", "r")
    pheno_file = open(f"{input_dir}/pheno.txt", "r")
    cov_file = open(f"{input_dir}/cov.txt", "r")

    # make directory for encrypted data if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    g_file = open(f"{output_dir}/g.bin", "wb")
    m_file = open(f"{output_dir}/m.bin", "wb")
    p_file = open(f"{output_dir}/p.bin", "wb")

    num_lines = sum(1 for _ in open(f"{input_dir}/pheno.txt", "r"))
    for i in range(num_lines):
        if i > 0 and num_lines > 10 and i % (num_lines // 10) == 0:
            print(f"Finished encrypting {i} lines out of {num_lines} lines")

        p = pheno_file.readline().rstrip().split() + cov_file.readline().rstrip().split()
        p = [str((int(x) - prng.next()) % prng.base_p) for x in p]

        geno_line = geno_file.readline().rstrip().split()
        g = [[-prng.next() % prng.base_p for _ in range(len(geno_line))] for _ in range(3)]
        m = [-prng.next() % prng.base_p for _ in range(len(geno_line))]
        for j, val in enumerate(geno_line):
            if val == "0":
                g[0][j] = (g[0][j] + 1) % prng.base_p
            elif val == "1":
                g[1][j] = (g[1][j] + 1) % prng.base_p
            elif val == "2":
                g[2][j] = (g[2][j] + 1) % prng.base_p
            else:
                m[j] = (m[j] + 1) % prng.base_p

        g_text = " ".join(map(str, g[0])) + " " + " ".join(map(str, g[1])) + " " + " ".join(map(str, g[2])) + "\n"
        g_file.write(g_text.encode("utf-8"))
        m_file.write((" ".join([str(x) for x in m]) + "\n").encode("utf-8"))
        p_file.write((" ".join(p) + "\n").encode("utf-8"))

    geno_file.close()
    pheno_file.close()
    cov_file.close()

    g_file.close()
    m_file.close()
    p_file.close()


def get_shared_mpcgwas_keys(my_private_key: PrivateKey, other_public_key: PublicKey, debug: bool = False) -> list:
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
    shared_key_1 = box.encrypt(message, nonce=nonce.to_bytes(24, byteorder="big")).ciphertext[16:]
    # python library has extra 16 bytes at beginning; see https://doc.libsodium.org/secret-key_cryptography/secretbox#notes
    nonce += 1
    if debug:
        print("nonce in hex: ", nonce.to_bytes(24, byteorder="big").hex())
    shared_key_2 = box.encrypt(message, nonce=nonce.to_bytes(24, byteorder="big")).ciphertext[16:]

    if debug:
        print("Role 1's Key:", shared_key_1.hex())
        print("Role 2's Key:", shared_key_2.hex())

    return [None, shared_key_1, shared_key_2]


def encrypt_data() -> None:
    username: str = get_username()
    doc_ref_dict: dict = get_doc_ref_dict()
    role = doc_ref_dict["participants"].index(username)

    other_public_key_str = get_other_user_public_key(doc_ref_dict, role)

    other_public_key = PublicKey(other_public_key_str, encoder=HexEncoder)  # type: ignore

    print("Generating shared keys...")
    private_key_path = os.path.join(constants.SFKIT_DIR, "my_private_key.txt")
    with open(private_key_path, "r") as f:
        my_private_key = PrivateKey(f.readline().rstrip(), encoder=HexEncoder)  # type: ignore
    condition_or_fail(my_private_key != other_public_key, "Private and public keys must be different")

    shared_keys = get_shared_mpcgwas_keys(my_private_key, other_public_key)

    input_dir_path = os.path.join(constants.SFKIT_DIR, "data_path.txt")
    with open(input_dir_path, "r") as f:
        input_dir = f.readline().rstrip()

    data_hash = checksumdir.dirhash(input_dir, "md5")
    condition_or_fail(
        data_hash == doc_ref_dict["personal_parameters"][username]["DATA_HASH"]["value"], "Data hash mismatch"
    )

    print("Encrypting data...")
    base_p: int = int(doc_ref_dict["advanced_parameters"]["BASE_P"]["value"])
    encrypt_GMP(
        PseudoRandomNumberGenerator(shared_keys[role], base_p), input_dir, output_dir=constants.ENCRYPTED_DATA_FOLDER
    )

    print("saving shared key")
    with open(os.path.join(constants.ENCRYPTED_DATA_FOLDER, "other_shared_key.bin"), "wb") as f:
        f.write(shared_keys[3 - role])
    print("copying over pos.txt")
    shutil.copyfile(f"{input_dir}/pos.txt", os.path.join(constants.ENCRYPTED_DATA_FOLDER, "pos.txt"))

    print("\n\nThe encryption is complete.")


def get_other_user_public_key(doc_ref_dict: dict, role: int) -> str:
    print("Downloading other party's public key...")

    other_role = 3 - role

    if len(doc_ref_dict["participants"]) != 3:
        print("Expected 2 participants (excluding Broad). Exiting.")
        sys.exit(1)

    i = 0
    while True:
        other_public_key_str = (
            doc_ref_dict["personal_parameters"][doc_ref_dict["participants"][other_role]]
            .get("PUBLIC_KEY", {})
            .get("value")
        )
        if other_public_key_str:
            break

        print("No public key found for other user. Waiting...")
        i += 1
        if i > 60:
            print("Failed to find public key for other user after 5 minutes. Exiting.")
            sys.exit(1)

        time.sleep(5)
        doc_ref_dict = get_doc_ref_dict()

    return other_public_key_str
