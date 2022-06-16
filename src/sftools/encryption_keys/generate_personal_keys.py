from nacl.encoding import HexEncoder
from nacl.public import PrivateKey


def generate_personal_keys():
    """
    Generate a new keypair, and save my_public_key.txt and my_private_key.txt.
    """
    # Generate a new keypair
    private_key = PrivateKey.generate()
    public_key = private_key.public_key

    with open("my_public_key.txt", "w") as f:
        f.write(public_key.encode(encoder=HexEncoder).decode())  # type: ignore

    with open("my_private_key.txt", "w") as f:
        f.write(private_key.encode(encoder=HexEncoder).decode())  # type: ignore

    print("Your public and private keys have been generated. Please upload my_public_key.txt to the Website.")


if __name__ == "__main__":
    generate_personal_keys()
