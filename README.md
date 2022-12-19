## sfkit

`sfkit` is a collection of CLI tools to help run certain types of federated and/or secure multi-party computation especially on genomic data. It is a companion to the website [here](https://sfkit.org/).

## Documentation

You can read the full documentation [here](https://sfkit.readthedocs.io/en/latest/).

## Prerequisites

[python3](https://www.python.org/downloads/)

## Installation

`pip install sfkit`

## Usage

Usage: sfkit <auth | networking | generate_keys | register_data | run_protocol>

- auth: Authenticate with the CLI.
- networking: Setup the networking, including your IP address and any relevant ports.
- generate_keys: Generate your public and private cryptographic keys for use in encrypting the data.
- register_data: Register and validate your data.
- run_protocol: Run the protocol. As this command may be long-running, you may want to run it with a tool like nohup, screen or tmux to prevent it from terminating if you close this window/terminal. For example, `nohup sfkit run_protocol & tail -f nohup.out`.

### Questions

If you have questions or concerns, you can reach me at [smendels@broadinstitute.org](mailto:smendels@broadinstitute.org).
