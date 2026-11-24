#!/bin/bash
set -e

echo "===================================================================="
echo "     MongoDB Security Lab: Docker Build & Push to Docker Hub        "
echo "===================================================================="

read -p "Enter your Docker Hub Username: " DOCKER_USER
if [ -z "$DOCKER_USER" ]; then
    echo "[ERROR] Docker Hub username cannot be empty."
    exit 1
fi

IMAGE_NAME="${DOCKER_USER}/mongodb-security-lab:latest"

echo ""
echo "[1/3] Building Docker image '${IMAGE_NAME}'..."
docker build -t "${IMAGE_NAME}" .

echo ""
echo "[2/3] Logging in to Docker Hub..."
docker login

echo ""
echo "[3/3] Pushing '${IMAGE_NAME}' to Docker Hub..."
docker push "${IMAGE_NAME}"

echo ""
echo "===================================================================="
echo "[SUCCESS] Image successfully published to Docker Hub!"
echo "Repository URL: https://hub.docker.com/r/${DOCKER_USER}/mongodb-security-lab"
echo ""
echo "Grader demonstration command:"
echo "  docker run -it -p 27017:27017 -p 27100:27100 ${IMAGE_NAME}"
echo "===================================================================="
