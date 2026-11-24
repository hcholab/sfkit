# Running an SF-SKAT study on sfkit

Oct 9, 2026 · @Haris

## Overview

An SF-SKAT study runs between two cohorts that hold data and one helper machine that sfkit starts for you. Each cohort runs one command on its own machine, and both end with the same table of gene-level Burden and SKAT p-values.

Individual-level data stays on each cohort's machine. The machines exchange encrypted intermediate values, each cohort's sample count, and the final p-values.

|  | Cohort A | Cohort B | Helper (CP0) |
| --- | --- | --- | --- |
| In this study | MVP | AoU | Started automatically |
| Data was prepared with | `secure-rvas prepare --party 1` | `secure-rvas prepare --party 2`, using Cohort A's public variant list | No data |
| On the sfkit website | Creates the study and sets the parameters | Joins the study | Shown as "Broad" |
| Receives the results | Yes | Yes | No |

The roles are fixed by how the data was prepared. The cohort that prepared as A must create the study, and the cohort that prepared as B must join it.

The work has five steps:

1. Both cohorts agree on the settings below.
2. Each cohort lays out its prepared data in the folder structure sfkit expects.
3. Cohort A creates the study, Cohort B joins, and Cohort A enters the parameters.
4. Both cohorts start sfkit and leave it running until it finishes.
5. Each cohort collects the results from its own data folder.

## Settings for this study

Both cohorts must use the same website, the same sfkit image and the same study parameters. The values below are the ones used in the successful test run on 9 October 2026; the study coordinator confirms the final ones.

| Setting | Value used in testing |
| --- | --- |
| sfkit website | https://dev.yale.sfkit.org |
| sfkit image | `ghcr.io/hcholab/sfkit:skat` |

Cohort A enters the study parameters on the website. They must describe the data both cohorts prepared.

| Parameter, as labelled on the website | What it must match | Test value |
| --- | --- | --- |
| Chromosomes | The chromosomes both cohorts prepared, comma-separated | `22` |
| Ancestries | The ancestry labels both cohorts prepared, comma-separated | `EUR` |
| Phenotype Columns | One name per column of `pheno.txt`, in order. The names label the results; the count must equal the number of columns. | `LDLC_final_mgdl_6sd_masked,HDLC_mgdl_6sd_masked` |
| Number of Covariates | The number of columns in `cov.txt` | `10` |
| Data Bits, Fractional Bits, Probes (under Advanced Parameters) | The protocol settings agreed for the study | `70`, `40`, `50` |
| MPC Threads (Advanced) | Number of parallel lanes. More lanes use more memory and network traffic. | `2` |
| CKKS Parameters, Random Seed (Advanced) | Leave at the defaults unless told otherwise | `PN14QP436S45`, `42` |
| Variant Masks, Max Minor Allele Frequency | Not used during the run. They only applied when the data was prepared. | Leave as shown |

Both cohorts must have the same phenotypes in the same column order, and the same number of covariates.

- [ ] Coordinator: confirm the website and image for the real run
- [ ] Coordinator: fill in the final study parameters

## What each cohort needs

Each cohort needs one Linux machine that can run Docker and reach the internet, plus its own account on the sfkit website.

| Requirement | Detail |
| --- | --- |
| Machine | Linux on x86-64. sfkit uses all of its CPU cores. |
| Docker | Installed, and you can run `docker` (with `sudo` if needed). |
| Outbound network | HTTPS to the sfkit website and to `ghcr.io`, and outbound UDP. No inbound ports need to be opened. |
| Website account | One per cohort. The two cohorts must sign in as different users. |
| The prepared data | On that machine, laid out as described in the next section. |
| A session that stays open | Run sfkit inside `tmux` or `screen`, because the command must keep running until the study finishes. |

Check Docker and the network before the day of the run:

```
docker run --rm hello-world
docker pull ghcr.io/hcholab/sfkit:skat
```

If either command fails, sort that out first. sfkit also checks the network itself when it starts and prints the result as `NAT type`.

## Lay out your data

Each cohort gives sfkit one data folder that contains a `prepared` folder in exactly the structure below. sfkit checks the structure when it starts and stops with a message if something is missing.

Cohort A (MVP), shown for ancestry `EUR` and chromosome 22:

```
<data folder>/
└── prepared/
    └── EUR/                    one folder per ancestry, in upper case
        └── chr22/              one folder per chromosome
            ├── genes.txt
            ├── block_sizes.txt
            └── A/
                ├── cov.txt
                ├── pheno.txt
                └── geno/
                    ├── block.0.bin
                    ├── block.1.bin
                    └── ...
```

Cohort B (AoU) uses `B` instead of `A` and has one extra folder, `private`:

```
<data folder>/
└── prepared/
    └── EUR/
        └── chr22/
            ├── genes.txt
            ├── block_sizes.txt
            └── B/
                ├── cov.txt
                ├── pheno.txt
                ├── geno/
                │   ├── block.0.bin
                │   └── ...
                └── private/
                    ├── block.0.bin
                    └── ...
```

Repeat the `chr<N>` folder for every chromosome, and the ancestry folder for every ancestry, listed in the study parameters.

| File | What it holds |
| --- | --- |
| `genes.txt` | One gene ID per line. The line order numbers the genes from 0. |
| `block_sizes.txt` | One number per line: how many public variants the gene on the same line has. |
| `geno/block.<i>.bin` | Genotypes of gene `i` at the public variants, one byte per sample and variant. |
| `private/block.<i>.bin` (Cohort B only) | Cohort B's additional variants for gene `i`. The file may be empty but must exist. |
| `cov.txt` | One row per sample, one column per covariate. Numbers only, no header, no intercept column. |
| `pheno.txt` | One row per sample, one column per phenotype. Numbers only, no header. |

These files are what `secure-rvas prepare` writes, so you should not need to edit them. `genes.txt` and `block_sizes.txt` come out identical at both cohorts when Cohort B prepared with Cohort A's public variant list.

### Put the files in place

The folders must contain real files. `secure-rvas prepare` can write links into a separate cache folder instead, and those links break inside Docker. Copying with `-L` turns them into real files:

```
DATA=/path/to/skat-data
mkdir -p "$DATA"
cp -rL /path/to/secure-rvas-run-dir/prepared "$DATA/"
chmod -R o+rX "$DATA"
chmod o+w "$DATA"
```

The two `chmod` lines matter. sfkit runs as a different user inside Docker, so it needs permission to read the data and to write the results into `$DATA/secure` and `$DATA/metrics`.

### Check it

Run this for one chromosome folder. Use `B` instead of `A` at Cohort B.

```
cd "$DATA/prepared/EUR/chr22"
wc -l genes.txt block_sizes.txt     # same number of lines
head -1 A/cov.txt | wc -w           # equals Number of Covariates
head -1 A/pheno.txt | wc -w         # equals the number of phenotype names
wc -l A/cov.txt A/pheno.txt         # same number of lines: your sample count
ls A/geno | wc -l                   # one block per gene
```

## Set up the study on the website

Cohort A creates the study and Cohort B joins it; the order decides who is which party, so do not swap it.

### Cohort A creates the study

1. Sign in to the sfkit website and open the studies page.
2. Click **Create New Study** and choose **SF-SKAT**.
3. Enter a study title. Leave **Demo Study** unticked.
4. Tick **Private Study** if only invited people should be able to see and join it.
5. Submit. The **Study Parameters** window opens; you can fill it in now or return to it later.

### Cohort B joins

1. Sign in with a different account from Cohort A.
2. Join in one of two ways:
   - Public study: find it in the list and click **Request to Join Study**. Cohort A then clicks **Approve Request** under Requested Participants.
   - Private study: Cohort A clicks **Invite New Study Participant** and enters Cohort B's email. Cohort B signs in with that email and accepts.
3. The study should now list three participants: Broad (the helper), Cohort A and Cohort B.

### Cohort A enters the parameters

1. On the study page, click **Study Parameters**.
2. Enter your own sample count in the **Number of Individuals** field that carries your name.
3. Fill in the parameters from the settings table above. Open **Advanced Parameters** for Data Bits, Fractional Bits, Probes and MPC Threads.
4. Click **Save changes**.

Only the study creator can edit the shared parameters. Cohort B should open the same window and check that the values match its own data.

### Both cohorts download their key

1. On the study page, click **Download Auth Key**. This saves `auth_key.txt`.
2. Copy the file to the machine that will run sfkit.
3. Note the address shown on the study page in the line that starts `export SFKIT_API_URL=`. You need it in the next section.

Each cohort has its own key. Treat it like a password: it lets its holder act as you in this study.

The study page also shows an example `docker run` command. Use the command in this guide instead, because the one on the page is written for a different setup.

## Run

Both cohorts run the same command, each on its own machine, and leave it running until it reports that it has finished. Either cohort can start first; the first one waits for the other.

Start a `tmux` or `screen` session, go to the folder that holds your `auth_key.txt`, and run:

```
chmod o+r auth_key.txt
export SFKIT_API_URL=<address from the study page>
DATA=/path/to/skat-data

docker run --rm -it --pull always \
  -v "$DATA":/data \
  -v "$PWD/auth_key.txt":/sfkit/auth_key.txt:ro \
  -e SFKIT_API_URL="$SFKIT_API_URL" \
  ghcr.io/hcholab/sfkit:skat all --data_path /data
```

`DATA` must be the full path of the data folder from the previous section. Add `sudo` in front of `docker` if your machine needs it.

The run passes through these stages. Waiting at stages 4 to 6 is normal.

| Stage | What you see | What it is waiting for |
| --- | --- | --- |
| 1. Sign-in | `Successfully authenticated with study ...` | Nothing |
| 2. Network check | `NAT type: Endpoint-Independent Mapping` | Nothing |
| 3. Data check | `Successfully registered and validated data!` | Nothing |
| 4. Other cohort | `Other participant(s) not yet ready. Waiting...` | The other cohort to start and pass its data check |
| 5. Helper | `No public key found for Broad. Waiting...` | The helper machine to start, usually 5 to 10 minutes |
| 6. Sync | `Waiting for all participants to sync up...` | All three parties to be ready |
| 7. Computation | Network setup, `CollectiveInit`, then timings per chromosome | The computation itself |
| 8. Finish | A timing summary ending in `TOTAL`, then `Finished SF-SKAT` | The other parties to finish too |

A few `Connection failed ... Retrying` lines at the start of stage 7 are normal. When the run is over, the study page shows **Finished protocol!** for all three participants.

In the test, with 100 samples per cohort and 3 genes, stage 7 took under a minute. No timing has been measured yet for a full-size run.

## Results

Each cohort finds the results in its own data folder, and both cohorts receive the same table. The helper receives nothing.

| File, under your data folder | Content |
| --- | --- |
| `secure/<ANCESTRY>/all_secure_results.tsv` | All chromosomes for that ancestry, one row per gene and phenotype |
| `secure/<ANCESTRY>/chr<N>.tsv` | The same rows for one chromosome |
| `metrics/<ANCESTRY>/metrics_party<N>.csv` | Timings and the number of bytes your machine sent and received |

The results table has these columns:

| Column | Meaning |
| --- | --- |
| `chromosome` | Chromosome number |
| `gene_index`, `gene_id` | Position of the gene in `genes.txt`, and its ID |
| `phenotype_index`, `phenotype_name` | Position of the phenotype, and the name entered in the study parameters |
| `secure_burden_p` | Burden test p-value |
| `secure_skat_wh_p` | SKAT p-value |

By default, sfkit also uploads your results table to the sfkit website, where you can download it from the study page. That copy keeps only one ancestry, so treat the files in your data folder as the results of record.

The files are written by the Docker user, so you can read them but need `sudo` to move or delete them.

## If something goes wrong

Most problems show up in the first minute as a line starting with `FAILED`, both in your terminal and on the study page. Find the message below, fix the cause, then start over as described at the end.

| Message | Cause | What to do |
| --- | --- | --- |
| `Could not find .../prepared/...` | The data folder does not match the expected structure, or the Chromosomes or Ancestries parameters name something you did not prepare. | Compare your folder with the layout section and the parameters with your data. |
| `... is a broken link` | The prepared folder contains links into a cache folder that Docker cannot see. | Copy the data again with `cp -rL`. |
| `num_cov does not match ...` | Number of Covariates differs from the columns in `cov.txt`. | Cohort A corrects the parameter, or the data is re-prepared. |
| `phenotype_columns does not match ...` | The number of phenotype names differs from the columns in `pheno.txt`. | Cohort A corrects the parameter, or the data is re-prepared. |
| `... have different number of rows` | The prepared files do not belong together. | Prepare the data again. |
| `... must be writable to store SF-SKAT results` | sfkit cannot write into the folder it names, often `secure` or `metrics` left from an earlier run. | Run `chmod o+w` on that folder, or remove it. |
| `Symmetric NAT detected` | Your network cannot make direct connections to the other machines. | Use a different network or machine, or ask your network administrator. |
| Nothing after `Setting up networking...` | Outbound UDP is blocked. | Ask your network administrator to allow it. |
| `22 is not of type 'string'` when saving parameters | The website currently rejects a single chromosome. | Tell the coordinator. A fix is waiting to be deployed. |
| `No public key found for Broad` for more than 15 minutes | The helper machine did not start. | Tell the coordinator; it needs action on the website's side. |
| `Other participant(s) not yet ready` for a long time | The other cohort has not started, or failed its data check. | Contact the other cohort. |
| `Connection State has changed state=Failed`, or `Connection failed ... Retrying` that never stops | The machines could not reach each other. | Tell the coordinator and send your terminal output. |

### Starting over

A run cannot be resumed; it starts again from the beginning.

1. Both cohorts stop sfkit with Ctrl-C.
2. Cohort A clicks **Restart Study** on the study page.
3. Both cohorts run the same command again.

The study parameters and both `auth_key.txt` files stay valid after a restart.

When you ask the coordinator for help, send the last 50 lines of your terminal output and say which cohort you are.
