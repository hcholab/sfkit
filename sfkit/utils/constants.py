import os

WEBSITE_URL = "https://sfkit.org"
METADATA_VM_IDENTITY_URL = (
    "http://metadata.google.internal/computeMetadata/v1/"
    "instance/service-accounts/default/identity?"
    "audience={}&format={}&licenses={}"
)
BLOCKS_MODE = "usingblocks-"
SFKIT_DIR = os.environ.get("SFKIT_DIR", os.path.join(os.path.expanduser("~"), ".config", "sfkit"))
AUTH_FILE = os.path.join(SFKIT_DIR, "auth.txt")
AUTH_KEY = os.path.join(SFKIT_DIR, "auth_key.txt")
IS_DOCKER = os.path.exists("/.dockerenv")
SFKIT_PREFIX = "sfkit: "
OUT_FOLDER = os.path.join(os.environ.get("SFKIT_DIR", ""), "out")
ENCRYPTED_DATA_FOLDER = os.path.join(os.environ.get("SFKIT_DIR", ""), "encrypted_data")
