ARG PYTHON_VER=3.10


### Build SF-GWAS Go package
FROM golang:1.18 AS go

WORKDIR /src

RUN git clone -b main --depth 1 https://github.com/hcholab/sfgwas . && \
    go build && \
    mkdir cache


### Install C++ and Python dependencies, lint and test sfkit
FROM cgr.dev/chainguard/python:${PYTHON_VER}-dev AS py

ENV PATH="$PATH:/home/nonroot/.local/bin"
WORKDIR /build
USER root

# install Secure-GWAS package
RUN git clone --depth 1 https://github.com/hcholab/secure-gwas /secure-gwas && \
    # install pre-requisites
    apk add clang-15 curl gmp-dev libsodium-dev openssl-dev perl && \
    # compile NTL library
    mkdir /ntl && \
    curl -so- https://libntl.org/ntl-10.3.0.tar.gz \
    | tar -C /ntl -zxvf- --strip-components=1 && \
    cp /secure-gwas/code/NTL_mod/ZZ.h /ntl/include/NTL/ && \
    cp /secure-gwas/code/NTL_mod/ZZ.cpp /ntl/src/ && \
    cd /ntl/src && \
    ./configure NTL_THREAD_BOOST=on && \
    make -j$(nproc) all && \
    make install && \
    # compile Secure-GWAS
    cd /secure-gwas/code && COMP=$(which clang++) && \
    sed -i "s|^CPP.*$|CPP = ${COMP}|g" Makefile && \
    sed -i "s|^INCPATHS.*$|INCPATHS = -I/usr/local/include|g" Makefile && \
    sed -i "s|^LDPATH.*$|LDPATH = -L/usr/local/lib|g" Makefile && \
    make -j$(nproc) && \
    rm bin/GenerateKey bin/LogiRegClient

USER nonroot

# download Plink2
RUN curl -so plink2.zip https://s3.amazonaws.com/plink2-assets/alpha3/plink2_linux_avx2_20221024.zip && \
    unzip plink2.zip

# install dev Python dependencies globally
RUN python -m pip install --upgrade pip && \
    pip install flake8

# install runtime Python dependencies into the user lib folder
COPY requirements.txt .
RUN pip install -r requirements.txt --ignore-installed --user

# copy sources
COPY . .

# stop the build if there are Python syntax errors or undefined names
RUN flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# exit-zero treats all errors as warnings. The GitHub editor is 127 chars wide
RUN flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# run tests
RUN python -m pytest

# install sfkit for runtime use
RUN pip install . --user


### Copy libraries and executables into a minimal hardened runtime image
FROM cgr.dev/chainguard/python:${PYTHON_VER}

WORKDIR /app

ENV PATH="$PATH:."

COPY --from=go --chown=nonroot /src/cache ./cache
COPY --from=go /src/config ./config
COPY --from=go /src/scripts ./scripts
COPY --from=go /src/sfgwas /src/*.sh ./

COPY --from=py /secure-gwas/code/*.sh ./secure-gwas/code/
COPY --from=py /secure-gwas/code/bin ./secure-gwas/code/bin/
COPY --from=py /home/nonroot/.local/lib /usr/lib/libgmp.so.10 /usr/lib/libpcre2-8.so.0 /usr/lib/libsodium.so.23 /usr/lib/
COPY --from=py /home/nonroot/.local/bin/sfkit /usr/bin/awk /usr/bin/tee /usr/bin/xargs /build/plink2 /bin /bin/

ENTRYPOINT ["sfkit"]
