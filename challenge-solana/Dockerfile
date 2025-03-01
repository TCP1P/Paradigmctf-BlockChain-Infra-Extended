FROM gcr.io/paradigmxyz/ctf/solana-base:latest

WORKDIR /home/ctf/
COPY ./deploy/setup/package.json /home/ctf/setup/package.json
RUN cd setup && yarn
COPY ./deploy/ /home/ctf/
RUN cd setup && anchor build
RUN solana-keygen new --no-passphrase -o /root/.config/solana/id.json --force 
RUN solana config set -k /root/.config/solana/id.json
COPY ./tests/* /home/ctf/setup/tests/
