import os

WEBSITE_URL = "https://sfkit.org"
METADATA_VM_IDENTITY_URL = (
    "http://metadata.google.internal/computeMetadata/v1/"
    "instance/service-accounts/default/identity?"
    "audience={}&format={}&licenses={}"
)
SFKIT_DIR = os.path.expanduser("~/.config/sfkit")
AUTH_FILE = os.path.join(SFKIT_DIR, "auth.txt")
AUTH_KEY = os.path.join(SFKIT_DIR, "auth_key.txt")
