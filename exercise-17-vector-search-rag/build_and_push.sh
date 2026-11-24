#!/usr/bin/env bash
set -e

USERNAME="shashankreddy30"
IMAGE_NAME="mongodb-lab17"
TAG="latest"

echo "=========================================================="
echo "  Building and Pushing Lab 17 Demonstration Image"
echo "  Target Image: ${USERNAME}/${IMAGE_NAME}:${TAG}"
echo "  Docker Hub:   https://hub.docker.com/r/${USERNAME}/${IMAGE_NAME}"
echo "=========================================================="

echo "[1/3] Building Docker image..."
docker build -t "${USERNAME}/${IMAGE_NAME}:${TAG}" \
             -t "${USERNAME}/${IMAGE_NAME}:latest" \
             -t "shashankreddy30/nosql-lab17:latest" \
             -t "chintan/${IMAGE_NAME}:latest" \
             -t "${IMAGE_NAME}:latest" .

echo "[2/3] Pushing to Docker Hub..."
docker push "${USERNAME}/${IMAGE_NAME}:${TAG}"
docker push "shashankreddy30/nosql-lab17:latest"

echo "=========================================================="
echo "[SUCCESS] Image successfully published to Docker Hub!"
echo "Repository URL: https://hub.docker.com/r/${USERNAME}/${IMAGE_NAME}"
echo "Demonstration:  docker run --rm -it ${USERNAME}/${IMAGE_NAME}:${TAG} demo"
echo "=========================================================="
