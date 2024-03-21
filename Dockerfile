# hadolint global ignore=DL3006,DL3013,DL3018,DL3059

FROM golang:1.21 AS go

WORKDIR /build

# Use version arg to rebuild downstream images
# (which are otherwise cached) on each new commit
ARG VERSION


FROM go AS sfgwas
RUN git clone --depth 1 https://github.com/hcholab/sfgwas . && \
    CGO_ENABLED=0 go build && \
    mkdir cache && \
    rm -rf .git
RUN ln -s /usr/bin/python python3


FROM go as sf-relate
RUN git clone https://github.com/froelich/sf-relate . && \
    git checkout sf-kit && \
    go get relativeMatch && \
    go build && \
    go test -c -o sf-relate && \
    rm -rf .git
RUN ln -s /usr/bin/python python3


FROM go AS sfkit-proxy
RUN git clone https://github.com/hcholab/sfkit-proxy . && \
    git checkout 858e6ca && \
    CGO_ENABLED=0 go build


FROM cgr.dev/chainguard/python:latest-dev AS dev

WORKDIR /build

# hadolint ignore=DL3002
USER root

# hadolint global ignore=DL4006
SHELL ["/bin/ash", "-eo", "pipefail", "-c"]
ENV PIP_NO_CACHE_DIR=1

RUN apk add --no-cache curl wget make


FROM dev AS plink2
ARG MARCH=native
RUN ARCH=$(grep -q avx2 /proc/cpuinfo && [ "${MARCH}" = "native" ] || [ "${MARCH}" = "x86-64-v3" ] && echo "avx2" || echo "x86_64") && \
    curl -so plink2.zip "https://s3.amazonaws.com/plink2-assets/plink2_linux_${ARCH}_latest.zip" && \
    unzip plink2.zip


FROM dev AS secure-gwas

RUN apk add --no-cache clang-16-dev gmp-dev libclang-cpp-16 libsodium-dev libsodium-static openssl-dev perl

RUN git clone --depth 1 https://github.com/hcholab/secure-gwas . && \
    rm -rf .git

ARG MARCH=native

RUN mkdir /ntl && \
    curl -so- https://libntl.org/ntl-10.3.0.tar.gz | tar -C /ntl -zxvf- --strip-components=1 && \
    cp code/NTL_mod/ZZ.h /ntl/include/NTL/ && \
    cp code/NTL_mod/ZZ.cpp /ntl/src/

WORKDIR /ntl/src
RUN ./configure NTL_THREAD_BOOST=on CXXFLAGS="-g -O2 -march=${MARCH}" && \
    make "-j$(nproc)" all && \
    make install

WORKDIR /build/code
RUN COMP="$(which clang++)" && \
    sed -i "s|^CPP.*$|CPP = ${COMP}|g" Makefile && \
    sed -i "s|-march=native|-march=${MARCH} -maes -static|g" Makefile && \
    sed -i "s|^INCPATHS.*$|INCPATHS = -I/usr/local/include|g" Makefile && \
    sed -i "s|^LDPATH.*$|LDPATH = -L/usr/local/lib|g" Makefile && \
    make "-j$(nproc)"


FROM dev AS sfkit

RUN pip install poetry
RUN apk add --update zlib-dev

USER nonroot
COPY . .
RUN poetry install --only main,dev

RUN poetry run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude .venv
RUN poetry run flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics --exclude .venv
RUN poetry run pytest

RUN poetry build -f wheel

RUN poetry install --only main --sync


FROM us.gcr.io/broad-dsp-gcr-public/base/python:distroless

WORKDIR /sfkit

ENV PATH="$PATH:/sfkit:/sfkit/sfgwas:/sfkit/sf-relate:/home/nonroot/.local/bin" \
    PYTHONUNBUFFERED=TRUE \
    SFKIT_DIR="/sfkit/.sfkit" \
    SFKIT_PROXY_ON=TRUE 

# hadolint ignore=DL3022
COPY --from=cgr.dev/chainguard/bash     /bin /usr/bin   /bin/
COPY --from=plink2      --chown=nonroot /build/plink2   ./
COPY --from=secure-gwas --chown=nonroot /build          ./secure-gwas/
COPY --from=sfgwas      --chown=nonroot /build          ./sfgwas/
COPY --from=sf-relate    --chown=nonroot /build          ./sf-relate/
COPY --from=sfkit-proxy --chown=nonroot /build/*-proxy  ./

COPY --from=sfkit /build/.venv/lib /usr/lib/
COPY --from=sfkit /build/dist/sfkit*.whl ./

RUN python -m pip install --no-cache-dir --user ./*.whl

ENTRYPOINT ["sfkit"]
