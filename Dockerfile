# hadolint global ignore=DL3006,DL3013,DL3018,DL3041,DL3059
ARG WORK=/sfkit

# -------------------- base -------------------- #
FROM registry.access.redhat.com/ubi9/python-312-minimal AS base

# hadolint ignore=DL3002
USER root

RUN echo install_weak_deps=0 >> /etc/dnf/dnf.conf && \
    curl -O https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm && \
    rpm -ivh ./*.rpm && \
    rm -f ./*.rpm && \
    microdnf upgrade -y && \
    microdnf install -y \
        libsodium && \
    microdnf clean all


# -------------------- go -------------------- #
FROM base AS go

ARG GO_VERSION=1.25.5

RUN microdnf install -y \
        git-core \
        go-toolset \
    && microdnf clean all

ARG WORK
WORKDIR ${WORK}


# -------------------- sfgwas -------------------- #
FROM go AS sfgwas

RUN git clone https://github.com/hcholab/sfgwas . && \
    git checkout 2ad091d && \
    go build && \
    mkdir cache && \
    rm -rf .git


# -------------------- sfgwas-lmm -------------------- #
FROM go AS sfgwas-lmm

RUN git clone --depth 1 https://github.com/hhcho/sfgwas-lmm . && \
    git checkout 2025e02 && \
    go test -c -o scripts/sfgwas-lmm ./lmm && \
    rm -rf .git


# -------------------- sf-relate -------------------- #
FROM go AS sf-relate

RUN git clone https://github.com/froelich/sf-relate . && \
    git checkout 9d1a076 && \
    go get relativeMatch && \
    go build && \
    go test -c -o sf-relate && \
    rm -rf .git


# -------------------- sfkit-proxy -------------------- #
FROM go AS sfkit-proxy

SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

RUN git clone https://github.com/hcholab/sfkit-proxy . && \
    git checkout 14eba92 && \
    go build && \
    # ensure FIPS is enabled, fail if not
    go get github.com/acardace/fips-detect && \
    go run github.com/acardace/fips-detect sfkit-proxy \
    | grep -E 'FIPS-capable Go binary.*Yes'


# -------------------- dev -------------------- #
FROM base AS dev

ARG WORK
WORKDIR ${WORK}

# -------------------- plink -------------------- #
FROM dev AS plink

ARG MARCH=native

RUN microdnf install -y unzip && \
    microdnf clean all && \
    ARCH=$(grep -q avx2 /proc/cpuinfo && [ "${MARCH}" = "native" ] || [ "${MARCH}" = "x86-64-v3" ] && echo "avx2" || echo "x86_64") && \
    curl -so plink2.zip "https://s3.amazonaws.com/plink2-assets/plink2_linux_${ARCH}_latest.zip" && \
    unzip plink2.zip plink2 && \
    curl -so plink.zip "https://s3.amazonaws.com/plink1-assets/plink_linux_x86_64_latest.zip" && \
    unzip plink.zip plink && \
    rm ./*.zip


# -------------------- c++ & ntl -------------------- #
FROM dev AS cpp

RUN microdnf install -y \
        clang \
        git-core \
        gmp-devel \
        libsodium-devel \
        openssl-devel \
        perl \
        tar \
    && microdnf clean all

SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

WORKDIR /ntl
RUN curl -so- https://libntl.org/ntl-10.3.0.tar.gz | tar -C /ntl -zxvf- --strip-components=1 && \
    NTL_MOD_URL="https://raw.githubusercontent.com/hcholab/secure-gwas/refs/heads/master/code/NTL_mod" && \
    curl -s "${NTL_MOD_URL}/ZZ.h" -o /ntl/include/NTL/ZZ.h && \
    curl -s "${NTL_MOD_URL}/ZZ.cpp" -o /ntl/src/ZZ.cpp

ARG MARCH=native

WORKDIR /ntl/src
RUN ./configure NTL_THREAD_BOOST=on CXXFLAGS="-g -O2 -march=${MARCH}" && \
    make "-j$(nproc)" all && \
    make install

ARG WORK
WORKDIR ${WORK}


# -------------------- secure-dti -------------------- #
FROM cpp AS secure-dti

RUN git clone --depth 1 -b cp-only https://github.com/hcholab/secure-dti . && \
    git checkout 8a49bdf3 && \
    rm -rf .git

ARG WORK
WORKDIR ${WORK}/mpc/code
RUN sed -i "s|^CPP.*$|CPP = /usr/bin/clang++|g" Makefile && \
    sed -i "s|^INCPATHS.*$|INCPATHS = -I/usr/local/include|g" Makefile && \
    sed -i "s|^LDPATH.*$|LDPATH = -L/usr/local/lib|g" Makefile && \
    sed -i "s|-march=native|-march=${MARCH} -maes|g" Makefile && \
    sed -i "s|c++11|c++14|g" Makefile && \
    sed -i '5i#include <stdint.h>' param.h && \
    make "-j$(nproc)" && \
    rm -rf build include lib


# -------------------- secure-gwas -------------------- #
FROM cpp AS secure-gwas

RUN git clone --depth 1 https://github.com/hcholab/secure-gwas . && \
    git checkout d4c6dbc && \
    rm -rf .git

ARG WORK
WORKDIR ${WORK}/code
RUN sed -i "s|^LDPATH.*$|LDPATH = -L/usr/local/lib|g" Makefile && \
    sed -i "s|-march=native|-march=${MARCH} -maes|g" Makefile && \
    make "-j$(nproc)" && \
    rm -rf build


# -------------------- sfkit package -------------------- #
FROM dev AS sfkit

ENV PIP_NO_CACHE_DIR=1

RUN microdnf install -y gcc g++ python3.12-devel zlib-devel && \
    microdnf clean all && \
    pip install poetry==2.4.1

COPY poetry.* pyproject.toml ./
RUN poetry install --only main,dev --no-root

COPY . .
RUN poetry install --only-root

RUN poetry run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude .venv
RUN poetry run flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics --exclude .venv
RUN poetry run pytest

RUN poetry sync --only main
RUN poetry build -f wheel
RUN .venv/bin/pip install --no-deps --no-index dist/*.whl


# -------------------- final image -------------------- #
FROM base

ARG USER=sfkit \
    WORK

WORKDIR ${WORK}

RUN microdnf install -y proxychains-ng && \
    microdnf clean all && \
    adduser $USER && \
    chown -R $USER:$USER .

ENV HOME=${WORK} \
    OPENSSL_FORCE_FIPS_MODE=1 \
    PATH="${WORK}/.venv/bin:$PATH:${WORK}:${WORK}/sfgwas:${WORK}/sf-relate:${WORK}/sfgwas-lmm/scripts" \
    PYTHONPATH="${WORK}/.venv/lib/python3.12/site-packages:${WORK}/.venv/lib64/python3.12/site-packages" \
    PYTHONUNBUFFERED=TRUE \
    PYTHONWARNINGS="ignore:pkg_resources is deprecated as an API:UserWarning" \
    SFKIT_DIR="${WORK}/.sfkit"

USER $USER

COPY --from=plink       --chown=$USER ${WORK}/plink*    ./
COPY --from=secure-dti  --chown=$USER ${WORK}           ./secure-dti/
COPY --from=secure-gwas --chown=$USER ${WORK}           ./secure-gwas/
COPY --from=sfgwas      --chown=$USER ${WORK}           ./sfgwas/
COPY --from=sfgwas-lmm  --chown=$USER ${WORK}           ./sfgwas-lmm/
COPY --from=sf-relate   --chown=$USER ${WORK}           ./sf-relate/
COPY --from=sfkit-proxy --chown=$USER ${WORK}/*-proxy   ./

COPY --from=sfkit --chown=$USER ${WORK}/dist/sfkit*.whl ./
COPY --from=sfkit --chown=$USER ${WORK}/.venv/ .venv/

ENTRYPOINT ["sfkit"]
