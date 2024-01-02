#!/bin/bash

set -e

(cd challenge-base && docker build  . -t gcr.io/paradigmxyz/ctf/base:latest)
(cd eth-deps && docker build  . -t gcr.io/paradigmxyz/ctf/eth-deps:latest)
(cd eth-challenge-base && docker build  . -t gcr.io/paradigmxyz/ctf/eth-base:latest)
