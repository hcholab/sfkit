## Cryptographic Keys and Encryption for Secure GWAS Website

This repository is made to facilitate offline key exchange and encryption before the online DataSharing and GWAS analysis. The goal is to make it easier for researchers to share data and conduct GWAS analysis without every having to upload unencrypted data to the server.

## Installation and Usage

1. Download the respository with `git clone https://github.com/broadinstitute/key-exchange.git`
2. Install the dependencies with `pip install -r requirements.txt` (you can optionally create a [virtual environment](https://docs.python.org/3/library/venv.html) before doing this; this is the recommended practice if you have multiple python environments that you would like to keep separate)
3. Put your data in the `input_data/` directory.
4. Run `python3 generate_personal_keys.py` to generate your personal keys.
5. Upload your public key to the project page of the [Secure-GWAS website](https://secure-gwas-website-bhj5a4wkqa-uc.a.run.app/index).
6. Once you have the other participant's public key, run `python3 encrypt_data.py` to encrypt your data.
7. Upload your encrypted data to your Google Cloud Bucket.

You are now ready to conduct your GWAS analysis!

### Questions

If you have questions or concerns, you can reach me at [smendels@broadinstitute.org](mailto:smendels@broadinstitute.org).
