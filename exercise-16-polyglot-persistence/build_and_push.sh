#!/usr/bin/env bash
set -e

USERNAME="shashankreddy30"
IMAGE="mongodb-lab16"
TAG="latest"

echo "=========================================================="
echo "  Building and Pushing Lab 16 Polyglot Docker Image"
echo "  Target: ${USERNAME}/${IMAGE}:${TAG}"
echo "=========================================================="

docker build -t "${USERNAME}/${IMAGE}:${TAG}" \
             -t "${USERNAME}/${IMAGE}:latest" \
             -t "shashankreddy30/nosql-lab16:latest" \
             -t "chintan/${IMAGE}:latest" \
             -t "${IMAGE}:latest" .

docker push "${USERNAME}/${IMAGE}:${TAG}"
docker push "shashankreddy30/nosql-lab16:latest"

echo "=========================================================="
echo "[SUCCESS] Docker image pushed to https://hub.docker.com/r/${USERNAME}/${IMAGE}"
echo "=========================================================="
