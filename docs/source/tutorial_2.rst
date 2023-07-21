Tutorial 2 (Examples with two users)
====================================

.. note::

    There is also a website-only *auto-configured* version of this tutorial available at `sfkit.org/tutorial#2-person-tutorial <https://sfkit.org/tutorial#2-person-tutorial>`_.

Introduction
------------

This two-person tutorial is designed to guide you and a partner through the process of running a study using real genomic data with the *user-configured* option.  You'll both download sample data, configure your respective parts of the study, and execute a workflow together. For the purposes of this tutorial, we will refer to the two users as "User 1" and "User 2".

Tip: If you haven't already, we recommend that you go through Tutorial 1 first, as this tutorial will assume you have some familiarity with the basics of the workflow.

.. note::

    You can complete this tutorial on your own, but it's designed for two separate users.  To achieve this, you will need two independent browser sessions. We also recommend you have two independent compute environments, but this is not strictly necessary if you are careful about authenticating each user separately.


Website
-------

For the set up stage of this tutorial, please follow the same instructions as in the *auto-configured* version, available at `sfkit.org/tutorial <https://sfkit.org/tutorial#2-person-tutorial>`_. The only difference is that when you create the study, you should select the *user-configured* option instead of the *auto-configured* option. Then, when you get up to the part of the tutorial where it describes how to configure the study, you should follow the instructions below instead of the ones on the website.

Compute Environment
-------------------

Please follow the instructions described in :doc:`tutorial` to set up your compute environment.  (Each user needs to do this.) This includes setting up machines that can communicate with one another and installing sfkit as described in :doc:`installation`.

At this point, each user should have a compute environment with sfkit installed, the sample data auth_key.txt downloaded, and networking set up so that the two users can communicate with each other.

CLI
---

The commands that each user will need to run will be similar to those in :doc:`tutorial`.

1. Run

.. tab:: pip

    .. code-block:: console

        $ sfkit auth

.. tab:: docker

    .. code-block:: console

        $ docker run --rm -it --pull always \
            -v $PWD/sfkit:/sfkit/.sfkit \
            -v $PWD/auth_key.txt:/sfkit/auth_key.txt:ro \
            ghcr.io/hcholab/sfkit auth


2. Run

.. tab:: pip

    .. code-block:: console

        $ sfkit networking

.. tab:: docker

    .. code-block:: console

        $ docker run --rm -it --pull always \
            -v $PWD/sfkit:/sfkit/.sfkit \
            ghcr.io/hcholab/sfkit networking

For User 1, this will prompt the user to input a port they will use to communicate with User 2.  The port provided should be the lower end of a range of open ports for communication (e.g. 8100 for a range of 8100-8120).  User 1 can alternatively specify the port in the command line using the ``--ports`` flag.

3. Run

.. tab:: pip

    .. code-block:: console

        $ sfkit generate_keys

.. tab:: docker

    .. code-block:: console

        $ docker run --rm -it --pull always \
            -v $PWD/sfkit:/sfkit/.sfkit \
            ghcr.io/hcholab/sfkit generate_keys

4. Run

.. tab:: pip

    .. code-block:: console

        $ sfkit register_data

    You can optionally use the ``--data_path`` and ``--geno_binary_file_prefix`` flags if you want to specify them in the command line.  Otherwise, you will be prompted to enter them.

.. tab:: docker

    .. code-block:: console

        $ docker run --rm -it --pull always \
            -v $PWD/sfkit:/sfkit/.sfkit \
            -v $PWD/data:/sfkit/data \
            ghcr.io/hcholab/sfkit register_data

5. Run

.. tab:: pip

    .. code-block:: console

        $ sfkit run_protocol

    You can view the output on your study page of the website or directly in the ``sfgwas/out`` directory.

.. tab:: docker

    .. code-block:: console

        $ docker run --rm -it --pull always \
            -v $PWD/sfkit:/sfkit/.sfkit \
            -v $PWD/data:/sfkit/data \
            -p 8100-8120:8100-8120 \
            ghcr.io/hcholab/sfkit run_protocol

    You can view the output on your study page of the website or directly in the ``sfkit/out`` directory.

    The port range is only necessary for User 1 and should reflect the range from the `networking` command.


Congratulations! You have successfully completed the *user-configured* Tutorial 2.  You should have a better understanding of how to configure and execute a study using sfkit. Feel free to explore other `workflows <https://sfkit.org/workflows>`__ and data types or to use the platform for your own research projects.