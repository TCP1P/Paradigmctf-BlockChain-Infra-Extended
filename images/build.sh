#!/bin/bash

(cd challenge-base && docker build  . -t gcr.io/paradigmxyz/ctf/base:latest)
(cd eth-challenge-base && docker build  . -t gcr.io/paradigmxyz/ctf/eth-base:latest)
# (cd cairo-challenge-base && docker build  . -t gcr.io/paradigmxyz/ctf/cairo-base:latest)
