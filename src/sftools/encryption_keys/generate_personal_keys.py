import os

from google.cloud import firestore
from nacl.encoding import HexEncoder
from nacl.public import PrivateKey
from sftools.protocol.utils import constants
from sftools.protocol.utils.google_cloud_pubsub import GoogleCloudPubsub


def generate_personal_keys():
    """
    Generate and save a new keypair (public and private keys) for the user.
    """
    private_key = PrivateKey.generate()
    public_key = private_key.public_key.encode(encoder=HexEncoder).decode()

    public_key_path = os.path.join(constants.SFTOOLS_DIR, "my_public_key.txt")
    with open(public_key_path, "w") as f:
        f.write(public_key + "\n")

    private_key_path = os.path.join(constants.SFTOOLS_DIR, "my_private_key.txt")
    with open(private_key_path, "w") as f:
        f.write(private_key.encode(encoder=HexEncoder).decode() + "\n")  # type: ignore

    with open(constants.AUTH_FILE, "r") as f:
        email = f.readline().rstrip()
        study_title = f.readline().rstrip()

    doc_ref = firestore.Client().collection("studies").document(study_title.replace(" ", "").lower())
    doc_ref_dict = doc_ref.get().to_dict() or {}  # type: ignore
    role: str = str(doc_ref_dict["participants"].index(email))
    gcloudPubsub = GoogleCloudPubsub(constants.SERVER_GCP_PROJECT, role, study_title)
    gcloudPubsub.publish(f"update_firestore::public_key={public_key}::{study_title}::{email}")
    print(f"Your public and private keys have been generated and saved to {constants.SFTOOLS_DIR}.")
    print("Your public key has been uploaded to the website and is available for all participants in your study.")


def main():
    generate_personal_keys()


if __name__ == "__main__":
    main()
