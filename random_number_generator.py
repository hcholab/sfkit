import math
import random
import string

import nacl.secret

# taken from the secure-gwas repo
BASE_P = 1461501637330902918203684832716283019655932542929


class RandomNumberGenerator:
    """
    This custom Random Number Generator deterministically generates random
    numbers in the range of some prime in a cryptographically secure fashion.
    """

    def __init__(self, key, base_p=BASE_P):
        self.base_p = base_p
        self.box = nacl.secret.SecretBox(key)
        self.nonce = 1
        self.generate_buffer()

    def generate_buffer(self):
        self.nonce += 1
        random.seed(self.nonce)
        # the cyrptographic strength of this message is unimportant.
        # It really just needs to be a byte string of a reasonable length.
        msg = "".join(random.choices(string.ascii_lowercase, k=1000)).encode("utf-8")

        pseudo_random_byte_string = self.box.encrypt(
            msg, self.nonce.to_bytes(24, byteorder="big")
        ).ciphertext

        self.buffer = convert_byte_string_to_list_of_ints_in_range(
            pseudo_random_byte_string, self.base_p
        )

    def next(self):
        if not self.buffer:
            self.generate_buffer()
        return self.buffer.pop()


def convert_byte_string_to_list_of_ints_in_range(byte_string, max_value):
    res = []

    l = len(bin(max_value)) - 2  # get bit length of max_value
    n = math.ceil(l / 8)  # number of bytes we need to convert

    # pop first n bytes from byte_string
    while len(byte_string) >= n:
        cur = byte_string[:n]
        byte_string = byte_string[n:]

        # convert cur to int
        cur = int.from_bytes(cur, byteorder="big")
        # check if cur is in range; I can't just use the modulus as that would
        # lead to a non-uniform distribution for the numbers
        if cur <= max_value:
            res.append(cur)

    return res
