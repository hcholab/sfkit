# for MPC GWAS

import math

import nacl.secret

# some large prime; taken from the secure-gwas repo
BASE_P = 1461501637330902918203684832716283019655932542929

# some arbitrary string of length 1000; its content is not important to the efficacy/security of the encryption; in particular, it is okay to be deterministic like this
MESSAGE = b"neoiiztdnrzxokrhqnzlufoehvdknkflkypwvgnjzhfivnlecgzijiepozmiqnrqcaefhzusbymkzcrcxboozvtlvcylhpxemteaycpluxbezsiczcezzmdvibqraczxztvlaolphtiwogpinowxffviwkzapoqozozagnnzrnstxpvtidnajdmqxvvlsbzlzdcgnznhodcjxrjqigrcgzppcrfpidfwldtzbqzaaxkjeddmytjgfoekmvqvkixfthipaczpdcmlvucctxkmblpusybzsgyopzeedtqlhgbrbmfxcpdafktznmnrhhuzebmipynozsglrzaqbywexrvnudcxtelwhyarbvrsphefztdivytybagfcrqxbulgzndqgkoodgsxnntofscryscfkvgvlafvreabrymxpwhkbyjwetsehlwvaoiutqrdppydxcspzlkurijvbhjpoqosntdeofmmajydthafqubarwbngxydqpzjgtaotsgdqpelnfycvggoyxomgnqkcvosrirtelcdqhbfmtuvzoxmnrdbfltdohcitiutciyyxrzallhtjcqwqbxinckicdhvupwbnlkkvmmuoxlxhkflxhgqxoymevqfxihruqdqilqkydlrvzyvmrkncjdcrkudtjufzayhifjogywnyxfclqpyhdssrkwytnbdxlvwxwrsliymzlcvsjertgcychbzncgkhopawsufcefjwdveivduwphrkasigxtndyftmswovaxxkprxehscmflhmqkveqxlekpgrhnxpsgpmriibfeivotfbmkcwocsewxhusduzqgxbjfasutjwpdgntljntjgbrrozcfmbxbjkqihzytwdauznoofukgucmibfriisdqrqgxzjewyngwefvstvbibuylkbqcfjhqgvdhqqmatrwnjoxycejcxpqrbvwxqhkgnivjuuzylitpvfbmdwjdqhartpvcjookn"


class PseudoRandomNumberGenerator:
    """
    This custom Random Number Generator deterministically generates random
    numbers in the range of some prime in a cryptographically secure fashion.
    """

    def __init__(self, key, base_p=BASE_P):
        self.base_p = base_p
        self.box = nacl.secret.SecretBox(key)
        self.nonce = 0
        self.buffer = []

    def generate_buffer(self) -> None:
        """
        Generates a buffer of random numbers in the range of base_p
        """
        self.nonce += 1

        pseudo_random_byte_string = self.box.encrypt(MESSAGE, self.nonce.to_bytes(24, byteorder="big")).ciphertext[16:]
        # 16: because this encryption adds 16 bytes at the beginning, relative to the cpp implementation

        self.buffer = self.convert_byte_string_to_list_of_ints_in_range(pseudo_random_byte_string)

    def next(self) -> int:
        if not self.buffer:
            self.generate_buffer()
        return self.buffer.pop(0)

    def convert_byte_string_to_list_of_ints_in_range(self, byte_string) -> list:
        res = []

        l = len(bin(self.base_p)) - 2  # bit length; -2 to remove the "0b" prefix
        n = math.ceil(l / 8)  # number of bytes we need to convert

        # pop first n bytes from byte_string
        while len(byte_string) >= n:
            cur = list(byte_string[:n])
            byte_string = byte_string[n:]

            # if there are extra bits, we mask the first ones with 0
            if (n * 8) > l:
                diff = n * 8 - l
                # mask first diff bits as 0
                cur[0] = cur[0] & (1 << diff) - 1

            cur = int.from_bytes(cur, byteorder="big")

            # check if cur is in range; I can't just use the modulus as that would
            # lead to a non-uniform distribution for the numbers
            if cur <= self.base_p:
                res.append(cur)

        return res


def main() -> None:  # for testing
    key = bytes.fromhex("3a57393f2a2ef038d43b432c34339e0cd021a15ce25b17c8bf07a5d9eae05d13")
    prng = PseudoRandomNumberGenerator(key)
    for _ in range(2000):
        print(prng.next(), end=" ")


if __name__ == "__main__":
    # global debug
    # debug = len(sys.argv) > 1 and sys.argv[1] == "debug"

    main()
