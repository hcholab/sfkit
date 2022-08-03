import os

from google.cloud import firestore
from nacl.encoding import HexEncoder
from nacl.public import PrivateKey
from sfkit.protocol.utils import constants
from sfkit.protocol.utils.google_cloud_pubsub import GoogleCloudPubsub
from sfkit.protocol.utils.helper_functions import confirm_authentication


def generate_personal_keys():
    """
    Generate and save a new keypair (public and private keys) for the user.
    """
    private_key = PrivateKey.generate()
    public_key = private_key.public_key.encode(encoder=HexEncoder).decode()

    public_key_path = os.path.join(constants.sfkit_DIR, "my_public_key.txt")
    with open(public_key_path, "w") as f:
        f.write(public_key + "\n")

    private_key_path = os.path.join(constants.sfkit_DIR, "my_private_key.txt")
    with open(private_key_path, "w") as f:
        f.write(private_key.encode(encoder=HexEncoder).decode() + "\n")  # type: ignore

    email, study_title = confirm_authentication()

    doc_ref = firestore.Client().collection("studies").document(study_title.replace(" ", "").lower())
    doc_ref_dict = doc_ref.get().to_dict() or {}  # type: ignore
    role: str = str(doc_ref_dict["participants"].index(email))
    gcloudPubsub = GoogleCloudPubsub(constants.SERVER_GCP_PROJECT, role, study_title)
    gcloudPubsub.publish(f"update_firestore::PUBLIC_KEY={public_key}::{study_title}::{email}")
    print(f"Your public and private keys have been generated and saved to {constants.sfkit_DIR}.")
    print("Your public key has been uploaded to the website and is available for all participants in your study.")
