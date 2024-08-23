ARG BASE_IMAGE=python:3.12-slim
# hadolint ignore=DL3006
FROM ${BASE_IMAGE} as base

FROM base as builder
COPY . /code
RUN apt-get -qq -y update && \
    apt-get -qq -y install --no-install-recommends \
        git && \
    apt-get -y autoclean && \
    apt-get -y autoremove && \
    rm -rf /var/lib/apt-get/lists/* && \
    cd /code && \
    python -m pip install uv && \
    uv pip install --system --upgrade --no-cache pip wheel && \
    uv pip install --system --no-cache . && \
    python -m pip list

FROM base
COPY --from=builder /usr/local /usr/local
ENTRYPOINT pip list | grep Package && pip list | grep pylhe && /bin/sh
