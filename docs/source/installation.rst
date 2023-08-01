Installation
============

There are three primary ways to install the sfkit CLI - via Python's package manager, pip, via a `tar.gz` release download, or using a containerized Docker version. The ideal method for you will depend on your technical proficiency, requirements, and permissions on your machine.

The first option, pip, allows for a simpler, more straightforward installation process. However, it necessitates runtime installation of some dependencies (golang, plink2, sfgwas, etc.). This might pose a challenge if you don't have the necessary permissions to install these on your machine.

The second option is to download the `tar.gz` Release. This method is similar to the pip installation but utilizes a shell script to download and install sfkit directly from the latest GitHub release. It also has the significant advantage of bundling all the dependencies within the tar.gz, thus avoiding the need for their runtime installation.

The third option is to use Docker. 

All options require specific prerequisites, which we will outline in the following sections. Choose the one that best fits your use case and the resources available on your machine.



pip
---

**Prerequisites**

* **A Debian or Ubuntu-based system**

This is necessary because the sfkit CLI uses the ``apt`` package manager to install dependencies. If you don't have one on hand, your options include 1. obtaining one via, e.g. Google Cloud VM, 2. using the docker installation option, or 3. using the `auto-configured <https://sfkit.org/instructions>`__ version of sfkit.

* **Python3 and pip**

You can install Python3 and pip with the following command:

.. code-block:: console

    $ sudo apt-get install python3-pip -y


**Installation**

.. code-block:: console

    $ pip install -U sfkit


tar.gz Release
--------------

**Prerequisites**

* **Python3 and pip**

You can install Python3 and pip with the following command:

.. code-block:: console

    $ sudo apt-get install python3-pip -y

**Installation**

.. code-block:: console

    $ bash <(curl -sL https://github.com/hcholab/sfkit/releases/latest/download/install.sh)


docker
------

**Note**: The Docker image is designed and tested on a x86_64 architecture. If you would like to run sfkit on a different architecture, please reach out for assistance.

**Prerequisites**

The official docker installation instructions can be found at `docs.docker.com/get-docker <https://docs.docker.com/get-docker/>`__

Alternatively, on a linux machine you can run the following command to install docker:

.. code-block:: console

    $ curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh ./get-docker.sh

You may also need to run

.. code-block:: console

    $ sudo usermod -aG docker ${USER}

and then log out and log back in to be able to run docker commands without sudo.

**Usage**

When using the containerized version of sfkit, you will need to set up an ``sfkit`` directory to be shared with the container. This is where the sfkit CLI will store your authentication information and output from the protocol.

.. code-block:: console

    $ mkdir -p sfkit && chmod -R 777 sfkit

Running sfkit via docker is similar to running it directly from the command line, but with a few extra command-line arguments.

.. code-block:: console

    $ docker run --rm -it --pull always \
      -v $PWD/sfkit:/sfkit/.sfkit \
      -v $PWD/auth_key.txt:/sfkit/auth_key.txt:ro \
      -v $PWD/data:/sfkit/data \
      -p 8060-8080:8060-8080 \
      ghcr.io/hcholab/sfkit <auth | networking | generate_keys | register_data | run_protocol>

Here's a breakdown of each of these arguments:

* ``--rm``: Remove the container after it exits
* ``-it``: Run the container interactively
* ``--pull always``: Always pull the latest version of the container from GitHub
* ``-v $PWD/sfkit:/sfkit/.sfkit``: Mount the sfkit directory to the container's .sfkit directory. This is where the sfkit CLI will store your authentication information and output from the protocol.
* ``-v $PWD/auth_key.txt:/sfkit/auth_key.txt:ro``: This argument is used to mount the ``auth_key.txt`` file from your current directory on your host system to the ``/sfkit/auth_key.txt`` path within the Docker container. The ``auth_key.txt`` file, which needs to be downloaded from your study page on the `sfkit website <https://sfkit.org>`__, acts as a form of identification that confirms your association with the study. If your ``auth_key.txt`` file is located in a different directory, you'll need to adjust this path accordingly. This argument is only required when running the auth command.
* ``-v $PWD/data:/sfkit/data``: Mount the data directory in the current directory to the container's /sfkit/data directory. The data directory is where your input data should be placed (as explained in the Tutorial section). If your data directory is in a different location, you will need to change this argument accordingly. This argument is only necessary for the ``register_data`` and ``run_protocol`` commands.
* ``-p 8060-8080:8060-8080``: Expose ports 8060-8080 to the host machine. For a two-user study, this is only necessary for the first user. In general, you will need to expose ports according to the ports you set in the ``networking`` command, where the ports you set in the ``networking`` command are the lowest number of a small range (for faster communication). Of course, these ports also need to be open on the firewall of your machine. This argument is only necessary for the ``run_protocol`` command.
* ``ghcr.io/hcholab/sfkit``: This is the name of the Docker image in the Github Container Registry.
* ``<auth | networking | generate_keys | register_data | run_protocol>``: These are the commands you can run with the sfkit CLI. See the tutorials for examples of how to use each command.

Building the Docker Image Locally
---------------------------------

If you prefer to build the Docker image locally, you'll need to clone the sfkit repository and build the Docker image from the Dockerfile provided. Here's how you can do this:

**Prerequisites**

* **Docker**
* **Git**

**Building the Docker Image**

**Note**: The Docker image is designed and tested on a x86_64 architecture.

First, clone the sfkit repository:

.. code-block:: console

    $ git clone https://github.com/hcholab/sfkit sfkit_repo

Change into the sfkit directory:

.. code-block:: console

    $ cd sfkit_repo

Now, you can build the Docker image.

.. code-block:: console

    $ docker build . -t sfkit_local_image

Now you have the sfkit Docker image built and ready to use on your local machine.

**Usage**

The usage is the same as when pulling the image from the Github Container Registry, but now you don't need the ``--pull always`` argument, and you replace ``ghcr.io/hcholab/sfkit`` with the name you used for your local Docker image (in this case, ``sfkit_local_image``). Here's an example:

.. code-block:: console

    $ docker run --rm -it \
      -v $PWD/sfkit:/sfkit/.sfkit \
      -v $PWD/auth_key.txt:/sfkit/auth_key.txt:ro \
      -v $PWD/data:/sfkit/data \
      -p 8060-8080:8060-8080 \
      sfkit_local_image <auth | networking | generate_keys | register_data | run_protocol>

