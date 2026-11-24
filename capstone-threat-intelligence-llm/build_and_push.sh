#!/usr/bin/env bash
set -e

IMAGE_NAME="shashankreddy19318/threat-intel-app:latest"

echo "=========================================================="
echo "  Building Threat Intelligence LLM Platform Docker Image"
echo "=========================================================="
echo ">>> Building Docker image: $IMAGE_NAME"
docker build -t "$IMAGE_NAME" .

echo "[OK] Docker image built successfully!"
echo ">>> To push to Docker Hub, run:"
echo "    docker push $IMAGE_NAME"
