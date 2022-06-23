from google.cloud import firestore
from nacl.encoding import HexEncoder
from nacl.public import PrivateKey
from sftools.protocol.utils import constants
from sftools.protocol.utils.google_cloud_pubsub import GoogleCloudPubsub


def generate_personal_keys():
    """
    Generate a new keypair, and save my_public_key.txt and my_private_key.txt.
    """
    private_key = PrivateKey.generate()
    public_key = private_key.public_key.encode(encoder=HexEncoder).decode()

    with open("my_public_key.txt", "w") as f:
        f.write(public_key)

    with open("my_private_key.txt", "w") as f:
        f.write(private_key.encode(encoder=HexEncoder).decode())  # type: ignore

    with open("auth.txt", "r") as f:
        study_title = f.readline().rstrip()
        email = f.readline().rstrip()

    doc_ref = firestore.Client().collection("studies").document(study_title.replace(" ", "").lower())
    doc_ref_dict = doc_ref.get().to_dict() or {}  # type: ignore
    role: str = str(doc_ref_dict["participants"].index(email) + 1)
    gcloudPubsub = GoogleCloudPubsub(constants.SERVER_GCP_PROJECT, role, study_title)
    gcloudPubsub.publish(f"public_key={public_key}::{study_title}::{email}")
    print("Your public and private keys have been generated.")


def main():
    generate_personal_keys()


if __name__ == "__main__":
    main()
