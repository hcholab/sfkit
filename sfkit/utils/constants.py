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


def task_updates(num_power_iters: int) -> list:
    task_updates = [
        "Starting QC",
        "Starting PCA",
        "Preprocessing X",
    ]
    task_updates.extend(f"Power iteration iter  {i} / {num_power_iters}" for i in range(1, num_power_iters + 1))
    task_updates += [
        "Computing covariance matrix",
        "Eigen decomposition",
        "Extract PC subspace",
        "Finished PCA",
        "Starting association tests",
        "Starting QR",
        "Multiplication with genotype matrix started",
    ]
    task_updates += [f"MatMult: block {i} / 22 starting" for i in range(1, 23)]

    return task_updates


def transform(num_power_iters: int) -> dict:
    return (
        {
            "Starting QC": "Quality Control",
            "Starting PCA": "Principal Component Analysis",
            "Preprocessing X": "sub-task Preprocessing X",
        }
        | {
            f"Power iteration iter  {i} / {num_power_iters}": f"sub-task Power iteration iter {i} / {num_power_iters}"
            for i in range(1, num_power_iters + 1)
        }
        | {
            "Computing covariance matrix": "sub-task Computing covariance matrix",
            "Eigen decomposition": "sub-task Eigen decomposition",
            "Extract PC subspace": "sub-task Extract PC subspace",
            "Finished PCA": "sub-task Finished PCA",
            "Starting association tests": "Association Tests",
            "Starting QR": "sub-task Starting QR factorization",
            "Multiplication with genotype matrix started": "sub-task Multiplication with genotype matrix started",
        }
        | {f"MatMult: block {i} / 22 starting": f"sub-task MatMult: block {i} / 22 starting" for i in range(1, 23)}
    )
