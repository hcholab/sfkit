Workflows
=========

MPC-GWAS Workflow (2018 version)
--------------------------------

This workflows is based on the 2018 paper from nature biotechnology `Secure genome-wide association analysis using multiparty computation <https://www.nature.com/articles/nbt.4108>`__.  It is a complete workflow for GWAS analysis using `secret sharing <https://en.wikipedia.org/wiki/Secret_sharing>`__ to allow for `secure multiparty computation <https://en.wikipedia.org/wiki/Secure_multi-party_computation>`__.  

This workflow uses all of the currently supported :doc:`commands`.

SF-GWAS Workflow (2022 version)
-------------------------------

This workflow is based on "Secure and Federated Genome-Wide Association Studies for Biobank-Scale Datasets", which is currently under review (2022).  It is a complete workflow for GWAS analysis, and a significant speed-up improvement on the 2018 version.  It utilizes `homomorphic encryption <https://en.wikipedia.org/wiki/Homomorphic_encryption>`__ in addition to `secret sharing <https://en.wikipedia.org/wiki/Secret_sharing>`__.  

There are three major steps to the GWAS in this workflow.  The first step is the Quality Control (QC).  This filters out some lower quality data/samples.  The second step is the Population Stratification via Principal Component Analysis (PCA).  This step is meant to allow the GWAS to factor in/control for population differences when doing the associations.  The third step is the Association Tests.  This is where the actual associations between the phenotypes and genotypes are calculated.  

.. note::
    If you use the ``--phase`` flag, which phase you choose (1, 2 or 3) corresponds to the three major steps in the GWAS as just described.  If you do not use the ``--phase`` flag, then the workflow will run all three phases in order.

This workflow uses all of the currently supported :doc:`commands` except for *encrypt_data*.

See the :doc:`tutorial` for more information on how to use this workflow.

SF-PCA Workflow (2022 version)
------------------------------

This workflow consists of only Principal Component Analysis, using the same implementation as in the 2022 SF-GWAS workflow (phase 2).  It is generalized here as its own workflow to allow for PCA in domains other than GWAS.  