# hadolint global ignore=DL3006,DL3013,DL3018,DL3041,DL3059

# -------------------- base -------------------- #
FROM redhat/ubi9-minimal AS base


# -------------------- go -------------------- #
FROM base AS go

RUN microdnf install -y --setopt=install_weak_deps=0 \
        git-core \
        go-toolset \
    && microdnf clean all

WORKDIR /build


# -------------------- sfgwas -------------------- #
FROM go AS sfgwas

RUN git clone --depth 1 https://github.com/hcholab/sfgwas . && \
    git checkout db52ea4 && \
    go build && \
    mkdir cache && \
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
    git checkout fea99f1 && \
    go build && \
    # ensure FIPS is enabled, fail if not
    go get github.com/acardace/fips-detect && \
    go run github.com/acardace/fips-detect sfkit-proxy \
    | grep -E 'FIPS-capable Go binary.*Yes'


# -------------------- dev -------------------- #
FROM base AS dev

WORKDIR /build

# -------------------- plink2 -------------------- #
FROM dev AS plink2

ARG MARCH=native

RUN microdnf install -y unzip && \
    microdnf clean all && \
    ARCH=$(grep -q avx2 /proc/cpuinfo && [ "${MARCH}" = "native" ] || [ "${MARCH}" = "x86-64-v3" ] && echo "avx2" || echo "x86_64") && \
    curl -so plink2.zip "https://s3.amazonaws.com/plink2-assets/plink2_linux_${ARCH}_latest.zip" && \
    unzip plink2.zip


# -------------------- secure-gwas -------------------- #
FROM dev AS secure-gwas

RUN curl -O https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm && \
    rpm -ivh ./*.rpm && \
    microdnf install -y --setopt=install_weak_deps=0 \
        clang \
        git-core \
        gmp-devel \
        libsodium-devel \
        openssl-devel \
        perl \
        tar \
    && microdnf clean all \
    && rm -f ./*.rpm

RUN git clone --depth 1 https://github.com/hcholab/secure-gwas . && \
    git checkout d4c6dbc && \
    rm -rf .git

SHELL ["/bin/bash", "-eo", "pipefail", "-c"]
RUN mkdir /ntl && \
    curl -so- https://libntl.org/ntl-10.3.0.tar.gz | tar -C /ntl -zxvf- --strip-components=1 && \
    cp code/NTL_mod/ZZ.h /ntl/include/NTL/ && \
    cp code/NTL_mod/ZZ.cpp /ntl/src/

ARG MARCH=native

WORKDIR /ntl/src
RUN ./configure NTL_THREAD_BOOST=on CXXFLAGS="-g -O2 -march=${MARCH}" && \
    make "-j$(nproc)" all && \
    make install

WORKDIR /build/code
RUN sed -i "s|^CPP.*$|CPP = /usr/bin/clang++|g" Makefile && \
    sed -i "s|-march=native|-march=${MARCH} -maes|g" Makefile && \
    sed -i "s|^INCPATHS.*$|INCPATHS = -I/usr/local/include|g" Makefile && \
    sed -i "s|^LDPATH.*$|LDPATH = -L/usr/local/lib|g" Makefile && \
    make "-j$(nproc)"

# -------------------- sfkit package -------------------- #
FROM dev AS sfkit

ENV PIP_NO_CACHE_DIR=1

RUN microdnf install -y --setopt=install_weak_deps=0 python3-pip && \
    microdnf clean all && \
    pip install poetry

COPY . .
RUN poetry install --only main,dev

RUN poetry run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude .venv
RUN poetry run flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics --exclude .venv
RUN poetry run pytest

RUN poetry build -f wheel

RUN poetry install --only main --sync


# -------------------- final image -------------------- #
FROM base

WORKDIR /sfkit

ENV OPENSSL_FORCE_FIPS_MODE=1 \
    PATH="$PATH:/sfkit:/sfkit/sfgwas:/sfkit/sf-relate" \
    PYTHONUNBUFFERED=TRUE \
    SFKIT_DIR="/sfkit/.sfkit" \
    SFKIT_PROXY_ON=TRUE

COPY --from=base        --chown=nonroot \
    /lib64/ld-linux-x86-64.so.2 \
    /lib64/libc.so.6 \
    /lib64/libcrypto.so.3 \
    /lib64/libpthread.so.0 \
    /lib64/libssl.so.3 \
    /lib64/libstdc++.so.6 \
    ./lib/

COPY --from=plink2      --chown=nonroot /build/plink2   ./
COPY --from=secure-gwas --chown=nonroot /build          ./secure-gwas/
COPY --from=sfgwas      --chown=nonroot /build          ./sfgwas/
COPY --from=sf-relate   --chown=nonroot /build          ./sf-relate/
COPY --from=sfkit-proxy --chown=nonroot /build/*-proxy  ./

COPY --from=sfkit /build/.venv/lib          /usr/lib/
COPY --from=sfkit /build/.venv/lib64        /usr/lib64/
COPY --from=sfkit /build/dist/sfkit*.whl    ./

RUN microdnf install -y --setopt=install_weak_deps=0 \
        findutils \
        python3 \
        python3-pip \
    && \
    pip install --no-cache-dir ./*.whl && \
    microdnf remove -y python3-pip && \
    microdnf clean all \
    && \
    adduser nonroot && \
    chown -R nonroot:nonroot .

USER nonroot

ENTRYPOINT ["sfkit"]
