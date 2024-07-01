# hadolint global ignore=DL3006,DL3013,DL3018,DL3041,DL3059

FROM registry.access.redhat.com/ubi9/ubi-minimal AS base

FROM base AS go

RUN microdnf install -y --setopt=install_weak_deps=0 \
        git-core \
        go-toolset \
    && microdnf clean all

WORKDIR /build


FROM go AS sfgwas
RUN git clone --depth 1 https://github.com/hcholab/sfgwas . && \
    git checkout db52ea4 && \
    go build && \
    mkdir cache && \
    rm -rf .git
# RUN ln -s /usr/bin/python python3


FROM go as sf-relate
RUN git clone https://github.com/froelich/sf-relate . && \
    git checkout 9d1a076 && \
    go get relativeMatch && \
    go build && \
    go test -c -o sf-relate && \
    rm -rf .git
# RUN ln -s /usr/bin/python python3


FROM go AS sfkit-proxy
SHELL ["/bin/bash", "-eo", "pipefail", "-c"]
RUN git clone https://github.com/hcholab/sfkit-proxy . && \
    git checkout 3695077 && \
    go build && \
    # ensure FIPS is enabled, fail if not
    go get github.com/acardace/fips-detect && \
    go run github.com/acardace/fips-detect sfkit-proxy \
    | grep -E 'FIPS-capable Go binary.*Yes'


FROM base AS dev

WORKDIR /build

# # hadolint ignore=DL3002
# USER root


FROM dev AS plink2
ARG MARCH=native
RUN microdnf install -y unzip && \
    microdnf clean all && \
    ARCH=$(grep -q avx2 /proc/cpuinfo && [ "${MARCH}" = "native" ] || [ "${MARCH}" = "x86-64-v3" ] && echo "avx2" || echo "x86_64") && \
    curl -so plink2.zip "https://s3.amazonaws.com/plink2-assets/plink2_linux_${ARCH}_latest.zip" && \
    unzip plink2.zip


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


FROM dev AS sfkit

ENV PIP_NO_CACHE_DIR=1

RUN microdnf install -y --setopt=install_weak_deps=0 python3-pip && \
    microdnf clean all && \
    pip install poetry

# RUN apk add --no-cache zlib-dev

# USER nonroot
COPY . .
RUN poetry install --only main,dev

RUN poetry run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude .venv
RUN poetry run flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics --exclude .venv
RUN poetry run pytest

RUN poetry build -f wheel

RUN poetry install --only main --sync


FROM base

WORKDIR /sfkit

ENV OPENSSL_FORCE_FIPS_MODE=1 \
    PATH="$PATH:/sfkit:/sfkit/sfgwas:/sfkit/sf-relate" \
    PYTHONUNBUFFERED=TRUE \
    SFKIT_DIR="/sfkit/.sfkit" \
    SFKIT_PROXY_ON=TRUE

COPY --from=plink2      --chown=nonroot /build/plink2   ./
COPY --from=secure-gwas --chown=nonroot /build          ./secure-gwas/
COPY --from=sfgwas      --chown=nonroot /build          ./sfgwas/
COPY --from=sf-relate    --chown=nonroot /build          ./sf-relate/
COPY --from=sfkit-proxy --chown=nonroot /build/*-proxy  ./

COPY --from=sfkit /build/.venv/lib /usr/lib/
COPY --from=sfkit /build/dist/sfkit*.whl ./

RUN microdnf install -y --setopt=install_weak_deps=0 python3 python3-pip && \
    pip install --no-cache-dir ./*.whl && \
    microdnf remove -y python3-pip && \
    microdnf clean all && \
    adduser nonroot && \
    chown -R nonroot:nonroot .

USER nonroot

ENTRYPOINT ["sfkit"]
