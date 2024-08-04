FROM gcr.io/paradigmxyz/ctf/cairo-base:latest

COPY ./deploy/ /home/ctf/
COPY ./contracts/ /home/ctf/contracts/
WORKDIR /home/ctf/
RUN cd /home/ctf/contracts && /home/ctf/.local/bin/scarb build
