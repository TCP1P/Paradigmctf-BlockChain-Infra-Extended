FROM gcr.io/paradigmxyz/ctf/solana-base:latest

WORKDIR /home/ctf/
COPY ./setup/package.json ./setup/package.json
RUN cd setup && yarn
COPY ./setup/ /home/ctf/setup/
RUN cd setup && anchor keys sync && anchor build
COPY ./deploy/ /home/ctf/
RUN solana-keygen new --no-passphrase -o /root/.config/solana/id.json --force 
RUN solana config set -k /root/.config/solana/id.json
COPY ./tests/* /home/ctf/setup/tests/
