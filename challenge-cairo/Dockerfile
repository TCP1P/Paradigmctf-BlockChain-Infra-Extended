FROM dimasmaualana/cairo:latest

COPY ./deploy/ /home/ctf/
COPY ./contracts/ /home/ctf/contracts/
WORKDIR /home/ctf/
RUN cd /home/ctf/contracts && ~/.local/bin/scarb build
