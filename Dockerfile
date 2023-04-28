ARG PYTHON_VER=3.10


# Install dependencies, lint and test in a development image
FROM cgr.dev/chainguard/python:${PYTHON_VER}-dev AS dev

ENV PATH="$PATH:/home/nonroot/.local/bin"
WORKDIR /app

# install dev dependencies globally
RUN python -m pip install --upgrade pip && \
    pip install flake8

# install runtime dependencies into the user lib folder
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


# Copy libraries and executable into a minimal hardened runtime image
FROM cgr.dev/chainguard/python:${PYTHON_VER}

COPY --from=dev /home/nonroot/.local/lib /home/nonroot/.local/lib
COPY --from=dev /home/nonroot/.local/bin/sfkit /usr/local/bin/

ENTRYPOINT ["sfkit"]
