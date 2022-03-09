from nacl.encoding import HexEncoder
from nacl.public import PrivateKey


def main():
    """
    Generate a new keypair, print them to stdout, and save them to keys.txt
    """
    # Generate a new keypair
    private_key = PrivateKey.generate()
    public_key = private_key.public_key

    with open("my_public_key.txt", "w") as f:
        f.write(public_key.encode(encoder=HexEncoder).decode())  # type: ignore

    with open("my_private_key.txt", "w") as f:
        f.write(private_key.encode(encoder=HexEncoder).decode())  # type: ignore

    print(
        "Your public and private keys have been generated.  Please upload my_public_key.txt to the Secure GWAS website"
    )


if __name__ == "__main__":
    main()
