### Build SF-GWAS
FROM golang:1.18 AS sfgwas

WORKDIR /build

# compile Go code
RUN git clone --depth 1 https://github.com/hcholab/sfgwas . && \
    go build && \
    mkdir cache && \
    rm -rf .git

# create missing python3 alias needed by shell scripts
RUN ln -s /usr/bin/python python3


### Use Python development base image
FROM cgr.dev/chainguard/python:latest-dev AS dev

WORKDIR /build
USER root

# install common prerequisites
RUN apk add curl gmp-dev libsodium-dev


### Bulid Secure-GWAS
FROM dev AS secure-gwas

# install toolchain
RUN apk add clang-15 openssl-dev perl

# download source
RUN git clone --depth 1 https://github.com/hcholab/secure-gwas . && \
    rm -rf .git

# compile NTL with Secure-GWAS mods
ARG MARCH=native
RUN mkdir /ntl && \
    curl -so- https://libntl.org/ntl-10.3.0.tar.gz | tar -C /ntl -zxvf- --strip-components=1 && \
    cp /build/code/NTL_mod/ZZ.h /ntl/include/NTL/ && \
    cp /build/code/NTL_mod/ZZ.cpp /ntl/src/ && \
    cd /ntl/src && \
    ./configure NTL_THREAD_BOOST=on CXXFLAGS="-g -O2 -march=${MARCH}" && \
    make -j$(nproc) all && \
    make install

# patch and compile Secure-GWAS
RUN cd code && \
    COMP=$(which clang++) && \
    sed -i "s|^CPP.*$|CPP = ${COMP}|g" Makefile && \
    sed -i "s|-march=native|-march=${MARCH} -maes|g" Makefile && \
    sed -i "s|^INCPATHS.*$|INCPATHS = -I/usr/local/include|g" Makefile && \
    sed -i "s|^LDPATH.*$|LDPATH = -L/usr/local/lib|g" Makefile && \
    make -j$(nproc)


### Build SFKit
FROM dev AS sfkit

# install ldd tool for PyInstaller
RUN apk add posix-libc-utils

# download Plink2
RUN curl -so plink2.zip https://s3.amazonaws.com/plink2-assets/alpha3/plink2_linux_avx2_20221024.zip && \
    unzip plink2.zip

# install Python dependencies
RUN pip install hatch
COPY pyproject.toml .
RUN pip install $(hatch dep show requirements --all)

# copy sources
COPY . .

# stop the build if there are Python syntax errors or undefined names
RUN flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# exit-zero treats all errors as warnings. The GitHub editor is 127 chars wide
RUN flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# run tests
RUN python -m pytest

# install and compile sfkit for runtime use
RUN pip install .
RUN pyinstaller pyinstaller.spec


### Copy distributables into the minimal hardened runtime image
FROM cgr.dev/chainguard/bash

WORKDIR /sfkit

# for backwards compatibility
RUN ln -s $(pwd) /app

ENV PATH="$PATH:/sfkit:/sfkit/sfgwas" \
    SFKIT_DIR="/sfkit/.sfkit"

COPY --from=secure-gwas --chown=nonroot /build ./secure-gwas/
COPY --from=sfgwas      --chown=nonroot /build ./sfgwas/
COPY --from=sfkit       --chown=nonroot /build/dist/sfkit ./

ENTRYPOINT ["sfkit"]
