FROM gcr.io/paradigmxyz/ctf/eth-deps:latest as deps
FROM gcr.io/paradigmxyz/ctf/base:latest

ENV HTTP_PORT=8545
ENV PROXY_PORT=8080

COPY --from=deps /root/.foundry/* /bin/
COPY 96-start-launcher /startup
COPY 98-start-gunicorn /startup

COPY eth_sandbox /usr/lib/python/eth_sandbox

ENV PYTHONPATH /usr/lib/python
