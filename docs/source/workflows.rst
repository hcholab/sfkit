Workflows
=========

Genome-Wide Association Study (GWAS)
------------------------------------

GWAS is an essential study design in genetics for identifying genetic variants that are correlated with a biological trait of interest, such as disease status. Analyzing a large cohort of individuals is important for detecting variants that are rare or weakly associated with the trait. Our workflows below perform a GWAS jointly over datasets held by a group of collaborators to increase the power of the study, while keeping the input datasets private.

========
MPC-GWAS
========

This workflow implements a collaborative GWAS protocol based on secure multiparty computation (MPC) as described in `Secure genome-wide association analysis using multiparty computation <https://www.nature.com/articles/nbt.4108>`__ (Nature Biotechnology, 2018). It provides a standard GWAS pipeline including quality control filters (for missing data, allele frequencies, and Hardy-Weinberg equilibrium), population stratification analysis (based on principal component analysis), and association tests.

Each user provides an input dataset including genotypes, covariates, and a target phenotype for a local cohort of individuals. These data are encrypted and split into multiple copies (secret shares in MPC terminology), which are then distributed to collaborators before running the joint analysis. Unencrypted data is not shared with a server.

**Data Input**

* `geno.txt`: The genotype matrix, or minor allele dosage matrix, is stored as a tab-separated file in which the SNP values (i.e., features) are encoded as genotype scores (i.e., as 0, 1, or 2).
* `pos.txt`: This file must accompany the genotype matrix and stores the genomic positions of the SNPs in a 2-columns file where each row contains the chromosome number and the position in the chromosome of the corresponding SNP, separated by a tabulation.
* `cov.txt`: A tab-separated file storing the covariate matrix in which each row is a sample, and each column is a covariate, e.g., patient older than 50 years old. We assume all covariates are binary.
* `pheno.txt`: The phenotype vector, e.g., containing the infection status of each patient, is stored in a single-column file.

**Data Output**

* `assoc.txt`: The association statistics.
* `ikeep.txt`: QC filter results for individuals.
* `gkeep[1-2].txt`: QC filter results for SNPs.

This workflow currently supports joint analyses between pairs of collaborators. For studies involving more than two users, please use the SF-GWAS workflow.

=======
SF-GWAS
=======

This workflow implements a secure and federated (SF) protocol for collaborative GWAS, meaning that each input dataset remains with the data holder and only a smaller amount of intermediate results are exchanged in an encrypted form. Unlike MPC-GWAS, even the encrypted input dataset is never shared to minimize the computational overhead. Our federated GWAS algorithm is introduced in `Truly Privacy-Preserving Federated Analytics for Precision Medicine with Multiparty Homomorphic Encryption <https://www.nature.com/articles/s41467-021-25972-y>`__ (Nature Communications, 2021). Further improvements and extensions in a recent `preprint <https://www.biorxiv.org/content/10.1101/2022.11.30.518537v1>`__ are also incorporated to provide the state-of-the-art performance. Similar to MPC-GWAS, this GWAS pipeline includes quality control filters, population stratification analysis, and association tests.

.. note::
    If you use the ``--phase`` flag, which phase you choose (1, 2 or 3) corresponds to the three major steps in the GWAS as just described.  If you do not use the ``--phase`` flag, then the workflow will run all three phases in order.

Each user provides an input dataset including genotypes, covariates, and a target phenotype for a local cohort of individuals. The joint analysis protocol makes an efficient use of local computation on the unecrypted data while ensuring that only encrypted intermediate results are shared among the users.

**Data Input**

* `geno/chr[1-22].[pgen|psam|pvar]`: The genotype or minor allele dosage matrix is encoded using the PGEN file format for each chromosome. This format has been introduced in the standard PLINK2 tool for genomic data processing as an efficient way to store large-scale genomic datasets. Note that this file encodes the genomic positions of the SNPs directly.
* `sample_keep.txt`: This file accompanies the genotype matrix and lists the sample IDs from the .psam file to include in the analysis. This file is required to comply with the standard format proposed in PLINK2 (see the --keep option in the PLINK2 documentation).
* `pheno.txt`: As before, each line includes the phenotype under study for each sample.
* `cov.txt`: Each line includes a tab-separated list of covariates for each sample. Unlike in the previous workflow, the covariates and phenotypes in this workflow are not required to be binary.

**Data Output**

* `assoc.txt`: The association statistics.
* `gkeep.txt`: QC filter results for SNPs.

Principal Component Analysis (PCA)
----------------------------------

PCA is a standard algorithm for dimensionality reduction. In genetics, PCA is commonly applied to the genotype data to identify the population structure of a given cohort. Coordinates of each individual in a reduced space output by PCA represent their ancestry background in relation to other individuals. This information is useful for genetic analyses, for example for constructing additional covariates in GWAS.

======
SF-PCA
======

This workflow allows a group of users to perform a PCA jointly on their private datasets to obtain a desired number of top principal components (PCs) without sharing the data. This corresponds to one of the steps in GWAS workflows described above, here provided as a standalone workflow, based on the secure and federated (SF) approach. Each user provides a matrix with the same number of columns (features) as the input. The workflow securely computes and returns the PCs of the pooled matrix while keeping any sensitive data encrypted at all times.

**Data Input**

* `data.txt`: The input matrix is stored as a tab-separated file in which each row is a sample, and each column is a feature, e.g., a SNP.

**Data Output**

* `Qpc.txt`: The top PCs of the pooled matrix.
