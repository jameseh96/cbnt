#!/bin/sh

set -e

docker build -f Dockerfile -t cbnt_client ../../../../

tag=$(date +%Y%m%d)
echo "To tag and upload to Docker Hub (tagged with today's date) run:"
echo ""
echo "    docker login"
echo "    docker tag cbnt_client:latest couchbaseeng/cbnt_client:${tag}"
echo "    docker push couchbaseeng/cbnt_client:${tag}"
