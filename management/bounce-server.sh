#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd "$DIR"/../deployment/docker/server
docker stop cbnt_server
docker rm cbnt_server
docker build -f Dockerfile -t timbradgate/cbnt_server ../../../
docker run -p 0.0.0.0:2222:22 -p 0.0.0.0:80:8000 -v ~/cbnt_data:/lnt/db --name=cbnt_server -d timbradgate/cbnt_server
