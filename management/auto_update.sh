#!/usr/bin/env bash

last_error=0

function fatal_error_handler() {
    last_error=$?
    echo "Fatal error - aborting"
    exit $last_error
}

timestamp() {
  date +"%D-%T"
}

trap fatal_error_handler ERR

cd ../..
mkdir -p cbnt_data_backups
sudo tar czfv cbnt_data_backups/backup-$(timestamp).tar cbnt_data/

cd cbnt/management
./node-offline.py

cd ../deployment/docker/server
git fetch --all
git reset --hard origin/master

docker stop cbnt_server
docker rm cbnt_server
docker build -f Dockerfile -t timbradgate/cbnt_server ../../../
docker run -p 0.0.0.0:2222:22 -p 0.0.0.0:80:8000 -v ~/cbnt_data:/lnt/db --name=cbnt_server -d timbradgate/cbnt_server

cd ../../../management
./node-online.py