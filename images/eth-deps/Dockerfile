FROM python:3.12

RUN true \
    && curl -L https://foundry.paradigm.xyz | bash \
    && bash -c "source /root/.bashrc && foundryup" \
    && chmod 755 -R /root \
    && true

RUN git config --global user.email "root@localhost"  && \
    git config --global user.name "root"

RUN mkdir /tmp/init
RUN cd /tmp/init && \
    /root/.foundry/bin/forge init && \
    /root/.foundry/bin/forge test && \
    rm -rf /tmp/init
