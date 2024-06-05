FROM gcr.io/paradigmxyz/ctf/eth-deps:latest as deps
FROM gcr.io/paradigmxyz/ctf/base:latest

ENV HTTP_PORT=8545
ENV PROXY_PORT=8080

COPY --from=deps /root/.foundry/* /bin/
COPY 96-start-launcher /startup
COPY 98-start-gunicorn /startup

# Uncomment the following lines to install dos2unix if needed
# RUN dos2unix /startup/98-start-gunicorn
# RUN dos2unix /startup/97-start-proxy
# RUN apt-get update && \
#     apt-get install -y dos2unix && \
#     rm -rf /var/lib/apt/lists/*


COPY eth_sandbox /usr/lib/python/eth_sandbox

ENV PYTHONPATH /usr/lib/python
