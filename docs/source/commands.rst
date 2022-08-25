Commands 
========

Here are the commands provided by sfkit.  See :doc:`usage` for which commands you need depending on your workflow.

.. _auth:

auth 
----

Authenticate with the CLI.

.. code-block:: console

   (.venv) $ sfkit auth

.. _setup networking:

setup_networking
----------------

Setup the networking, including your IP address and any relevant ports.

.. code-block:: console

   (.venv) $ sfkit networking

.. _generate personal keys:

generate_personal_keys
----------------------

Generate your public and private cryptographic keys for use in encrypting the data.

.. code-block:: console

   (.venv) $ sfkit generate_keys

.. _register data:

register_data
-------------

Register and validate your data.

.. code-block:: console

   (.venv) $ sfkit register_data

.. _encrypt data:

encrypt_data
------------

Encrypt your data (used only in the MPC GWAS protocol).

.. code-block:: console

   (.venv) $ sfkit encrypt_data

.. _run protocol:

run_protocol
------------

Run the protocol. As this command may be long-running, it is recommended that you run it using nohup or a tool like screen or tmux to prevent it from terminating if you close this window/terminal. For example, :code:`nohup sfkit run_protocol`.

.. code-block:: console
   
   (.venv) $ sfkit run_protocol