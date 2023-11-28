FROM gcr.io/paradigmxyz/ctf/base:latest

ENV HTTP_PORT=8545
ENV PROXY_PORT=8080

COPY requirements.txt /root

RUN python3 -m pip install -r /root/requirements.txt

RUN true \
    && curl -L https://foundry.paradigm.xyz | bash \
    && bash -c "source /root/.bashrc && foundryup" \
    && chmod 755 -R /root \
    && true

RUN mkdir /tmp/init && \
    cd /tmp/init && \
    /root/.foundry/bin/forge init && \
    /root/.foundry/bin/forge test && \
    rm -rf /tmp/init

COPY 98-start-gunicorn /startup
COPY 97-start-proxy /startup

COPY eth_sandbox /usr/lib/python/eth_sandbox

ENV PYTHONPATH /usr/lib/python
