import os
import shutil


def is_installed(binary: str) -> bool:
    return shutil.which(binary) is not None


SFKIT_API_URL = os.environ.get("SFKIT_API_URL", "https://sfkit.org/api")
TERRA_DEV_API_URL = "https://sfkit.dsde-dev.broadinstitute.org/api"
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
IS_INSTALLED_VIA_SCRIPT = is_installed("sfgwas") and is_installed("plink2") and is_installed("GwasClient")
EXECUTABLES_PREFIX = os.path.expanduser("~") + "/.local/" if IS_INSTALLED_VIA_SCRIPT else ""
SFKIT_PREFIX = "sfkit: "
OUT_FOLDER = os.path.join(os.environ.get("SFKIT_DIR", ""), "out")
ENCRYPTED_DATA_FOLDER = os.path.join(os.environ.get("SFKIT_DIR", ""), "encrypted_data")
SFKIT_PROXY_ON: bool = os.getenv('SFKIT_PROXY_ON', 'false').lower() == 'true'
