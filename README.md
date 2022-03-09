## Cryptographic Keys and Encryption for Secure GWAS Website

This repository is made to facilitate offline key exchange and encryption before the online DataSharing and GWAS analysis. The goal is to make it easier for researchers to share data and conduct GWAS analysis without every having to upload unencrypted data to the server.

## Prerequisites

If you don't already have them, you will need to install [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) and [python3](https://www.python.org/downloads/).

## Installation

1. Download the respository with `git clone https://github.com/simonjmendelsohn/secure-gwas-keys-and-encryption.git`
2. Enter the directory with `cd secure-gwas-keys-and-encryption`
3. Create and activate a python virtual environment with `python3 -m venv venv && source venv/bin/activate` (this step is optional but recommended)
4. Install the dependencies with `python -m pip install -r requirements.txt`

## Usage

1. Run `python generate_personal_keys.py` to generate your personal keys.
2. Upload your public key to the project page of the [Secure-GWAS website](https://secure-gwas-website-bhj5a4wkqa-uc.a.run.app/index).
3. Download the other participant's public key and put it in this repository.
4. Run `python encrypt_data.py` to encrypt your data.
5. Upload your encrypted data (the encrypted_data directory) to a Google Cloud Bucket.

You are now ready to conduct your GWAS analysis!

### Questions

If you have questions or concerns, you can reach me at [smendels@broadinstitute.org](mailto:smendels@broadinstitute.org).
