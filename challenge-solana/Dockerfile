FROM node:23 as builder

# Set working directory
WORKDIR /home/ctf

# Copy package files first to leverage Docker cache
COPY contracts/package.json contracts/package.json

# Install dependencies
RUN cd contracts && yarn

# Copy remaining source files
COPY contracts/ ./contracts/

# Final stage to reduce image size
FROM gcr.io/paradigmxyz/ctf/solana-base:latest

# Copy built artifacts from builder
COPY --from=builder /home/ctf/contracts/ /home/ctf/contracts/

WORKDIR /home/ctf/
RUN cd contracts && anchor build
COPY ./deploy/ /home/ctf/
RUN solana-keygen new --no-passphrase -o /root/.config/solana/id.json --force 
RUN solana config set -k /root/.config/solana/id.json
