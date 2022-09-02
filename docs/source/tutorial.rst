Tutorial (SF-GWAS Workflow (2022 version))
==========================================

Website
-------

1. Go to the companion `website <https://secure-gwas-website-bhj5a4wkqa-uc.a.run.app/>`_ and register or login.  
2. Create or join a study on the website.
3. Click on the "Configure Study" button, choose "User", and enter the Service Account Email where you are running the workflow.

CLI 
---

1. Install sfkit if you haven't already (see :doc:`installation`).

2. Run 

.. code-block:: console 
     
    (.venv) $ sfkit auth

3. Run 

.. code-block:: console 

    (.venv) $ sfkit networking

4. Run 

.. code-block:: console 
    
    (.venv) $ sfkit generate_keys

5. Run 

.. code-block:: console 
    
    (.venv) $ sfkit register_data

6. Run 

.. code-block:: console 
    
    (.venv) $ sfkit run_protocol

(This command should stall, waiting for other participants to be ready.)

**You have finished the demo!  Go ahead and try this process for a real study.**
