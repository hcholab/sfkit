### Build SF-GWAS
FROM golang:1.18 AS sfgwas

WORKDIR /build

# compile Go code
RUN git clone --depth 1 https://github.com/hcholab/sfgwas . && \
    # use static compilation
    CGO_ENABLED=0 go build && \
    mkdir cache && \
    rm -rf .git

# create missing python3 alias needed by shell scripts
RUN ln -s /usr/bin/python python3


### Use Python development base image
FROM cgr.dev/chainguard/python:latest-dev AS dev

WORKDIR /build
USER root

# install common prerequisite
RUN apk add --no-cache curl


### Download static Plink2 executable according to the platform
FROM dev AS plink2

ARG MARCH=native 

RUN ARCH=$(grep -q avx2 /proc/cpuinfo && [ "${MARCH}" == "native" ] || [ "${MARCH}" == "x86-64-v3" ] && echo "avx2" || echo "x86_64") && \
    curl -so plink2.zip "https://s3.amazonaws.com/plink2-assets/plink2_linux_${ARCH}_latest.zip" && \
    unzip plink2.zip


### Bulid Secure-GWAS
FROM dev AS secure-gwas

# install toolchain
RUN apk add --no-cache clang-15 gmp-dev libsodium-dev libsodium-static openssl-dev perl

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
    sed -i "s|-march=native|-march=${MARCH} -maes -static|g" Makefile && \
    sed -i "s|^INCPATHS.*$|INCPATHS = -I/usr/local/include|g" Makefile && \
    sed -i "s|^LDPATH.*$|LDPATH = -L/usr/local/lib|g" Makefile && \
    make -j$(nproc)


### Build SFKit
FROM dev AS sfkit

# install dev dependencies
RUN pip install hatch
COPY pyproject.toml .
RUN pip install $(hatch dep show requirements -f dev)

# copy sources
COPY . .

# stop the build if there are Python syntax errors or undefined names
RUN flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# exit-zero treats all errors as warnings. The GitHub editor is 127 chars wide
RUN flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# build and install sfkit wheel package as user for distribution
USER nonroot
RUN hatch build -t wheel
RUN pip install -I dist/sfkit*.whl

# run tests
RUN python -m pytest


### Copy distributables into a minimal hardened runtime image
FROM cgr.dev/chainguard/python

WORKDIR /sfkit

ENV PATH="$PATH:/sfkit:/sfkit/sfgwas" \
    SFKIT_DIR="/sfkit/.sfkit"

COPY --from=cgr.dev/chainguard/bash     /bin /usr/bin   /bin/
COPY --from=plink2      --chown=nonroot /build/plink2   ./
COPY --from=secure-gwas --chown=nonroot /build          ./secure-gwas/
COPY --from=sfgwas      --chown=nonroot /build          ./sfgwas/

COPY --from=sfkit /home/nonroot/.local/bin/sfkit /bin/
COPY --from=sfkit /home/nonroot/.local/lib /usr/lib/
COPY --from=sfkit /build/dist/sfkit*.whl ./

ENTRYPOINT ["sfkit"]
