## sftools

`sftools` is a collection of CLI tools to help run certain types of secure multi-party computation on genomic data. It is a companion to the website [here](https://secure-gwas-website-bhj5a4wkqa-uc.a.run.app/).

## Prerequisites

[python3](https://www.python.org/downloads/)

## Installation

`pip install sftools`

## Usage

Usage: sftools <auth | setup_networking | generate_personal_keys | register_data | encrypt_data | run_protocol>

- auth: Authenticate with the CLI.
- set_study (deprecated): Set the study you are using.
- setup_networking: Setup the networking, including your IP address and any relevant ports.
- generate_personal_keys: Generate your public and private cryptographic keys for use in encrypting the data.
- register_data: Register and validate your data.
- encrypt_data: Encrypt your data.
- run_protocol: Run the protocol. As this command may be long-running, it is recommended that you run it using nohup. This will prevent it from terminating if you close this window/terminal. For example, `nohup sftools run_protocol & tail -f nohup.out`. You can also use a tool like screen or tmux.

### Questions

If you have questions or concerns, you can reach me at [smendels@broadinstitute.org](mailto:smendels@broadinstitute.org).
