FROM python:3.7-alpine3.10
COPY . /code
RUN cd /code && \
    rm -rf /var/cache/apk/* && \
    python -m pip install --upgrade --no-cache-dir pip setuptools wheel && \
    python -m pip install --no-cache-dir . && \
    python -m pip list
ENTRYPOINT pip list | grep Package && pip list | grep pylhe && /bin/sh
