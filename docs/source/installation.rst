Installation 
============

There are two installation options for the sfkit CLI. The first is to install it directly from PyPI with pip. This is the simplest option. The second is to install a containerized version with docker. This option is slightly more involved, but has the benefit of not requiring any runtime installation. 

pip 
---

**Prerequisites**

* **A Debian or Ubuntu-based system** 

This is necessary because the sfkit CLI uses the ``apt`` package manager to install dependencies. If you don't have one on hand, your options include 1. obtaining one via, e.g. Google Cloud VM, 2. using the docker installation option, or 3. using the `auto-configured <https://sfkit.org/instructions>`__ version of sfkit.

* **Python 3.9 or later**

You can install Python with the following command:

.. code-block:: console 

    $ sudo apt-get install python3-pip -y


**Installation**

.. code-block:: console 
     
    $ pip install -U sfkit

docker
------

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

Running sfkit via docker is similar to running it directly from the command line, but with a few extra command-line arguments. For more details, please see the tutorials. 

.. code-block:: console 
  
    $ docker run --rm -it --pull always \
      -v $PWD/sfkit:/app/.sfkit \
      -v $PWD/auth_key.txt:/app/auth_key.txt:ro \
      -v $PWD/data:/app/data \
      -p 8060-8080:8060-8080 \
      ghcr.io/hcholab/sfkit <auth | networking | generate_keys | register_data | run_protocol>

Here's a breakdown of each of these arguments:

* ``--rm``: Remove the container after it exits
* ``-it``: Run the container interactively
* ``--pull always``: Always pull the latest version of the container from GitHub
* ``-v $PWD/sfkit:/app/.sfkit``: Mount the sfkit directory to the container's .sfkit directory. This is where the sfkit CLI will store your authentication information and output from the protocol.
* ``-v $PWD/auth_key.txt:/app/auth_key.txt:ro``: This argument is used to mount the ``auth_key.txt`` file from your current directory on your host system to the ``/app/auth_key.txt`` path within the Docker container. The ``auth_key.txt`` file, which needs to be downloaded from your study page on the `sfkit website <https://sfkit.org>`__, acts as a form of identification that confirms your association with the study. If your ``auth_key.txt`` file is located in a different directory, you'll need to adjust this path accordingly. This argument is only required when running the auth command.
* ``-v $PWD/data:/app/data``: Mount the data directory in the current directory to the container's /app/data directory. The data directory is where your input data should be placed (as explained in the Tutorial section). If your data directory is in a different location, you will need to change this argument accordingly. This argument is only necessary for the ``register_data`` and ``run_protocol`` commands.
* ``-p 8060-8080:8060-8080``: Expose ports 8060-8080 to the host machine. For a two-user study, this is only necessary for the first user. In general, you will need to expose ports according to the ports you set in the ``networking`` command, where the ports you set in the ``networking`` command are the lowest number of a small range (for faster communication). Of course, these ports also need to be open on the firewall of your machine. This argument is only necessary for the ``run_protocol`` command.

The last argument is the command you want to run. See the tutorials for examples of how to use each command.
