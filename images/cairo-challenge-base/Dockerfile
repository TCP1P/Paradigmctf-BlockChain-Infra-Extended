FROM shardlabs/starknet-devnet-rs as starknet
FROM gcr.io/paradigmxyz/ctf/base:latest


ENV HTTP_PORT=8545
ENV PROXY_PORT=8080

COPY --from=starknet /usr/local/bin/starknet-devnet /bin/starknet-devnet

USER ctf
ENV SHELL=/bin/bash
RUN curl --proto '=https' --tlsv1.2 -sSf https://docs.swmansion.com/scarb/install.sh | sh

USER root
COPY 96-start-launcher /startup
COPY 98-start-gunicorn /startup

# Uncomment the following lines to install dos2unix if needed
# RUN dos2unix /startup/98-start-gunicorn
# RUN dos2unix /startup/97-start-proxy
# RUN apt-get update && \
#     apt-get install -y dos2unix && \
#     rm -rf /var/lib/apt/lists/*


COPY cairo_sandbox /usr/lib/python/cairo_sandbox

ENV PYTHONPATH /usr/lib/python
