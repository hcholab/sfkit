import os
import sys

from google.cloud import firestore
from nacl.encoding import HexEncoder
from nacl.public import Box, PrivateKey, PublicKey
from sfkit.protocol.utils import constants
from sfkit.protocol.utils.helper_functions import confirm_authentication


def generate_shared_key():
    print("Generating shared key...")
    email, study_title = confirm_authentication()

    print("Downloading other party's public key...")
    doc_ref = firestore.Client().collection("studies").document(study_title.replace(" ", "").lower())
    doc_ref_dict = doc_ref.get().to_dict() or {}
    role = doc_ref_dict["participants"].index(email)
    other_public_key = doc_ref_dict["personal_parameters"][doc_ref_dict["participants"][3 - role]]["PUBLIC_KEY"][
        "value"
    ]
    if other_public_key == "":
        print("No public key found for other user. Exiting.")
        sys.exit(1)
    other_public_key = PublicKey(other_public_key, encoder=HexEncoder)

    private_key_path = os.path.join(constants.sfkit_DIR, "my_private_key.txt")
    with open(private_key_path, "r") as f:
        my_private_key = PrivateKey(f.readline().rstrip().encode(), encoder=HexEncoder)
    assert my_private_key != other_public_key, "Private and public keys must be different"

    shared_key = Box(my_private_key, other_public_key).shared_key()

    shared_key_path = os.path.join(constants.sfkit_DIR, "shared_key.txt")
    with open(shared_key_path, "w") as f:
        f.write(shared_key.hex() + "\n")

    print("Shared key generated.")
