FROM python:3.7-alpine3.10 as base

FROM base as builder
COPY . /code
RUN cd /code && \
    python -m pip install --upgrade --no-cache-dir pip setuptools wheel && \
    python -m pip install --no-cache-dir . && \
    python -m pip list

FROM base
COPY --from=builder /usr/local /usr/local
ENTRYPOINT pip list | grep Package && pip list | grep pylhe && /bin/sh
