#!/bin/bash

set -e

(cd challenge-base && docker build  . -t gcr.io/paradigmxyz/ctf/base:latest)
(cd challenge && docker build . -f Dockerfile.cairo -t gcr.io/paradigmxyz/ctf/cairo-base:latest)
(cd challenge && docker build . -f Dockerfile.eth -t gcr.io/paradigmxyz/ctf/eth-base:latest)
(cd challenge && docker build . -f Dockerfile.solana -t gcr.io/paradigmxyz/ctf/solana-base:latest)
