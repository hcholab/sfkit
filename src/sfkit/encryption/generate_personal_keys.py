import os

from nacl.encoding import HexEncoder
from nacl.public import PrivateKey

from sfkit.api import update_firestore
from sfkit.utils import constants
from sfkit.utils.helper_functions import authenticate_user


def generate_personal_keys() -> None:
    """
    Generate and save a new keypair (public and private keys) for the user.
    """
    authenticate_user()

    private_key: PrivateKey = PrivateKey.generate()
    public_key: str = private_key.public_key.encode(encoder=HexEncoder).decode()

    public_key_path: str = os.path.join(constants.SFKIT_DIR, "my_public_key.txt")
    os.makedirs(constants.SFKIT_DIR, exist_ok=True)
    with open(public_key_path, "w") as f:
        f.write(public_key + "\n")

    private_key_path = os.path.join(constants.SFKIT_DIR, "my_private_key.txt")
    with open(private_key_path, "w") as f:
        f.write(private_key.encode(encoder=HexEncoder).decode() + "\n")
    print(f"Your public and private keys have been generated and saved to {constants.SFKIT_DIR}.")

    update_firestore(f"update_firestore::PUBLIC_KEY={public_key}")
    print("Your public key has been uploaded to the website and is available for all participants in your study.")
