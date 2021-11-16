from nacl.encoding import HexEncoder
from nacl.public import PrivateKey


def main():
    """
    Generate a new keypair, print them to stdout, and save them to keys.txt
    """
    # Generate a new keypair
    private_key = PrivateKey.generate()
    public_key = private_key.public_key

    # print the keys
    print("Public key:", public_key.encode(encoder=HexEncoder).decode())
    print("Secret key:", private_key.encode(encoder=HexEncoder).decode())

    # Save the keypair to keys.txt
    with open("keys.txt", "w") as f:
        f.write(public_key.encode(encoder=HexEncoder).decode() + "\n")
        f.write(private_key.encode(encoder=HexEncoder).decode())

    print(
        "Please upload your public key to the project page on the Secure GWAS Website."
    )


if __name__ == "__main__":
    main()
