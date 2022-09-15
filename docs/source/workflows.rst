Workflows
=========

MPC-GWAS Workflow (2018 version)
--------------------------------

This workflows is based on the 2018 paper from nature biotechnology `Secure genome-wide association analysis using multiparty computation <https://www.nature.com/articles/nbt.4108>`__.  It is a complete workflow for GWAS analysis using `secret sharing <https://en.wikipedia.org/wiki/Secret_sharing>`__ to allow for `secure multiparty computation <https://en.wikipedia.org/wiki/Secure_multi-party_computation>`__.  

This workflow uses all of the currently supported :doc:`commands`.

SF-GWAS Workflow (2022 version)
-------------------------------

This workflow is based on "Secure and Federated Genome-Wide Association Studies for Biobank-Scale Datasets", which is currently under review (2022).  It is a complete workflow for GWAS analysis, and a significant speed-up improvement on the 2018 version.  It utilizes `homomorphic encryption <https://en.wikipedia.org/wiki/Homomorphic_encryption>`__ in addition to `secret sharing <https://en.wikipedia.org/wiki/Secret_sharing>`__.  

This workflow uses all of the currently supported :doc:`commands` except for *encrypt_data*.

See the :doc:`tutorial` for more information on how to use this workflow.

SF-PCA Workflow (2022 version)
------------------------------

*not yet implemented*