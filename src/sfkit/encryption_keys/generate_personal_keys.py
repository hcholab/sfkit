import os

from nacl.encoding import HexEncoder
from nacl.public import PrivateKey
from sfkit.protocol.utils import constants
from sfkit.protocol.utils.helper_functions import confirm_authentication
from sfkit.api import update_firestore


def generate_personal_keys(study_title: str = "") -> None:
    """
    Generate and save a new keypair (public and private keys) for the user.
    """
    private_key = PrivateKey.generate()
    public_key = private_key.public_key.encode(encoder=HexEncoder).decode()

    public_key_path = os.path.join(constants.SFKIT_DIR, "my_public_key.txt")
    os.makedirs(constants.SFKIT_DIR, exist_ok=True)
    with open(public_key_path, "w") as f:
        f.write(public_key + "\n")

    private_key_path = os.path.join(constants.SFKIT_DIR, "my_private_key.txt")
    with open(private_key_path, "w") as f:
        f.write(private_key.encode(encoder=HexEncoder).decode() + "\n")  # type: ignore

    if not study_title:
        email, study_title = confirm_authentication()
    else:
        email = "Broad"

    update_firestore(f"update_firestore::PUBLIC_KEY={public_key}::{study_title}::{email}")
    print(f"Your public and private keys have been generated and saved to {constants.SFKIT_DIR}.")
    print("Your public key has been uploaded to the website and is available for all participants in your study.")
