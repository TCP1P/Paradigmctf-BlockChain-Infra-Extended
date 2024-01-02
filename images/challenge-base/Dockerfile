FROM python:3.9.13

ENV PORT=31337

RUN true \
    && mkdir /var/log/ctf /startup \
    && apt update \
    && apt install -y xinetd tini \
    && rm -rf /var/cache/apt/archives \
    && useradd -m ctf \
    && true

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

# Install dos2unix
RUN apt-get update && \
    apt-get install -y dos2unix && \
    rm -rf /var/lib/apt/lists/*

COPY 00-create-xinetd-service /startup
COPY 99-start-xinetd /startup
COPY handler.sh /home/ctf/handler.sh
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh
RUN dos2unix /entrypoint.sh
RUN dos2unix /startup/00-create-xinetd-service
RUN dos2unix /startup/99-start-xinetd
RUN dos2unix /home/ctf/handler.sh

ENTRYPOINT ["tini", "-g", "--"]
CMD ["bash", "/entrypoint.sh"]
