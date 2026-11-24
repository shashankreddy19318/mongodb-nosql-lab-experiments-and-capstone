#!/usr/bin/env bash
# docker-build-push.sh
set -e

DOCKERHUB_USERNAME="${1:-chintan}"
TAG="${2:-latest}"
IMAGE_NAME="mongodb-lab14"
FULL_IMAGE="${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${TAG}"

echo "=========================================================="
echo "  Building and Pushing Lab 14 Demonstration Docker Image"
echo "  Target Image: ${FULL_IMAGE}"
echo "  Docker Hub:   https://hub.docker.com/r/${DOCKERHUB_USERNAME}/${IMAGE_NAME}"
echo "=========================================================="

echo "[1/2] Building Docker image..."
docker build -t "${FULL_IMAGE}" -t "${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest" -t "${IMAGE_NAME}:latest" .

echo "[2/2] Pushing image to Docker Hub..."
docker push "${FULL_IMAGE}"
if [ "${TAG}" != "latest" ]; then
    docker push "${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest"
fi

echo "=========================================================="
echo "[SUCCESS] Image uploaded to Docker Hub!"
echo "Image URL: https://hub.docker.com/r/${DOCKERHUB_USERNAME}/${IMAGE_NAME}"
echo "=========================================================="
