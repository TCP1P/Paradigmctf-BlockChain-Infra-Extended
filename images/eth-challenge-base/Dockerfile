FROM gcr.io/paradigmxyz/ctf/base:latest

ENV HTTP_PORT=8545
ENV PROXY_PORT=8080

COPY 98-start-gunicorn /startup
COPY 97-start-proxy /startup

COPY eth_sandbox /usr/lib/python/eth_sandbox

ENV PYTHONPATH /usr/lib/python
