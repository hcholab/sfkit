import os

WEBSITE_URL = "https://sfkit.org"
METADATA_VM_IDENTITY_URL = (
    "http://metadata.google.internal/computeMetadata/v1/"
    "instance/service-accounts/default/identity?"
    "audience={}&format={}&licenses={}"
)
BLOCKS_MODE = "usingblocks-"
SFKIT_DIR = os.path.expanduser("~/.config/sfkit")
AUTH_FILE = os.path.join(SFKIT_DIR, "auth.txt")
AUTH_KEY = os.path.join(SFKIT_DIR, "auth_key.txt")
IS_DOCKER = os.path.exists("/.dockerenv")
SFKIT_PREFIX = "sfkit: "
