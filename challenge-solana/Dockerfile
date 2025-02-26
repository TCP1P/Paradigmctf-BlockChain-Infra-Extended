FROM gcr.io/paradigmxyz/ctf/solana-base:latest

WORKDIR /home/ctf/
# RUN cd contracts && anchor build
COPY ./deploy/ /home/ctf/
RUN solana-keygen new --no-passphrase -o /root/.config/solana/id.json --force 
RUN solana config set -k /root/.config/solana/id.json
