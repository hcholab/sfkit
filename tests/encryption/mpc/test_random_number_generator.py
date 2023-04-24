# sourcery skip: avoid-single-character-names-variables, snake-case-functions
from sfkit.encryption.mpc.random_number_generator import PseudoRandomNumberGenerator


def test_PseudoRandomNumberGenerator():
    prng = PseudoRandomNumberGenerator(b"\x00" * 32, 1461501637330902918203684832716283019655932542929)
    for _ in range(10):
        prng.next()

    x = 1461501637330902918203684832716283019655932542930
    x_bytes = x.to_bytes(20, byteorder="big")
    prng.convert_byte_string_to_list_of_ints_in_range(x_bytes)

    prng = PseudoRandomNumberGenerator(b"\x00" * 32, base_p=17)
    prng.next()
