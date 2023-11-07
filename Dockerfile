# hadolint global ignore=DL3006,DL3013,DL3018,DL3059

### Base Golang image
FROM golang:1.21 AS go

WORKDIR /build

# Use version arg to rebuild downstream images
# (which are otherwise cached) on each new commit
ARG VERSION


### Build SF-GWAS
FROM go AS sfgwas

# compile Go code
RUN git clone --depth 1 https://github.com/hcholab/sfgwas . && \
    # use static compilation
    CGO_ENABLED=0 go build && \
    mkdir cache && \
    rm -rf .git

# create missing python3 alias needed by shell scripts
RUN ln -s /usr/bin/python python3


### Build sfkit-proxy
FROM go AS sfkit-proxy

# compile Go code
RUN git clone https://github.com/hcholab/sfkit-proxy . && \
    # use static compilation
    CGO_ENABLED=0 go build


### Use Python development base image
FROM cgr.dev/chainguard/python:latest-dev AS dev

WORKDIR /build

# hadolint ignore=DL3002
USER root

# hadolint global ignore=DL4006
SHELL ["/bin/ash", "-eo", "pipefail", "-c"]
ENV PIP_NO_CACHE_DIR=1

# install common prerequisite
RUN apk add --no-cache curl


### Download static Plink2 executable according to the platform
FROM dev AS plink2

ARG MARCH=native 
RUN ARCH=$(grep -q avx2 /proc/cpuinfo && [ "${MARCH}" = "native" ] || [ "${MARCH}" = "x86-64-v3" ] && echo "avx2" || echo "x86_64") && \
    curl -so plink2.zip "https://s3.amazonaws.com/plink2-assets/plink2_linux_${ARCH}_latest.zip" && \
    unzip plink2.zip


### Build Secure-GWAS
FROM dev AS secure-gwas

# install toolchain
RUN apk add --no-cache clang-16-dev gmp-dev libclang-cpp-16 libsodium-dev libsodium-static openssl-dev perl

# download source
RUN git clone --depth 1 https://github.com/hcholab/secure-gwas . && \
    rm -rf .git

# compile NTL with Secure-GWAS mods
ARG MARCH=native

# download and patch NTL sources
RUN mkdir /ntl && \
    curl -so- https://libntl.org/ntl-10.3.0.tar.gz | tar -C /ntl -zxvf- --strip-components=1 && \
    cp code/NTL_mod/ZZ.h /ntl/include/NTL/ && \
    cp code/NTL_mod/ZZ.cpp /ntl/src/

# install NTL
WORKDIR /ntl/src
RUN ./configure NTL_THREAD_BOOST=on CXXFLAGS="-g -O2 -march=${MARCH}" && \
    make "-j$(nproc)" all && \
    make install

# patch and compile Secure-GWAS
WORKDIR /build/code
RUN COMP="$(which clang++)" && \
    sed -i "s|^CPP.*$|CPP = ${COMP}|g" Makefile && \
    sed -i "s|-march=native|-march=${MARCH} -maes -static|g" Makefile && \
    sed -i "s|^INCPATHS.*$|INCPATHS = -I/usr/local/include|g" Makefile && \
    sed -i "s|^LDPATH.*$|LDPATH = -L/usr/local/lib|g" Makefile && \
    make "-j$(nproc)"


### Build SFKit
FROM dev AS sfkit

# set up Poetry
RUN pip install poetry

# copy sources and install dependencies as user
USER nonroot
COPY . .
RUN poetry install --only main,dev

# stop the build if there are Python syntax errors or undefined names
RUN poetry run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude .venv

# exit-zero treats all errors as warnings. The GitHub editor is 127 chars wide
RUN poetry run flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics --exclude .venv

# run tests
RUN poetry run pytest

# build and install sfkit wheel package for distribution
RUN poetry build -f wheel

# keep only runtime dependencies
RUN poetry install --only main --sync


### Copy distributables into a minimal hardened runtime image
FROM us.gcr.io/broad-dsp-gcr-public/base/python:distroless

WORKDIR /sfkit

ENV PATH="$PATH:/sfkit:/sfkit/sfgwas:/home/nonroot/.local/bin" \
    SFKIT_DIR="/sfkit/.sfkit"

# hadolint ignore=DL3022
COPY --from=cgr.dev/chainguard/bash     /bin /usr/bin   /bin/
COPY --from=plink2      --chown=nonroot /build/plink2   ./
COPY --from=secure-gwas --chown=nonroot /build          ./secure-gwas/
COPY --from=sfgwas      --chown=nonroot /build          ./sfgwas/
COPY --from=sfkit-proxy --chown=nonroot /build/*-proxy  ./

COPY --from=sfkit /build/.venv/lib /usr/lib/
COPY --from=sfkit /build/dist/sfkit*.whl ./

RUN python -m pip install --no-cache-dir --user ./*.whl

ENTRYPOINT ["sfkit"]
