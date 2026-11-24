#!/bin/bash
# docker-build-push.sh
# Automates building and pushing the Lab 13 Demonstration container to Docker Hub

set -e

DOCKERHUB_USERNAME="${1:-yourdockerhubusername}"
IMAGE_NAME="mongodb-replica-k8s-lab13"
TAG="${2:-latest}"
FULL_IMAGE="${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${TAG}"

echo "=========================================================="
echo "  Building & Pushing Lab 13 Docker Demonstration Image"
echo "  Target: https://hub.docker.com/r/${DOCKERHUB_USERNAME}/${IMAGE_NAME}"
echo "=========================================================="

if [ "$DOCKERHUB_USERNAME" == "yourdockerhubusername" ]; then
    echo "[USAGE] Please provide your Docker Hub username:"
    echo "        ./docker-build-push.sh <your-dockerhub-username> [tag]"
    echo ""
    echo "Example: ./docker-build-push.sh johndoe v1.0"
    exit 1
fi

# Step 1: Ensure keyfile exists
if [ ! -f keyfile ]; then
    echo "Generating keyfile before image build..."
    bash generate-keyfile.sh keyfile
fi

# Step 2: Build the image
echo ""
echo "[Step 1/3] Building Docker image: ${FULL_IMAGE} ..."
docker build -t "${FULL_IMAGE}" -t "${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest" .

# Step 3: Verify image locally
echo ""
echo "[Step 2/3] Verifying demonstration image locally..."
docker run --rm "${FULL_IMAGE}" --auto

# Step 4: Push to Docker Hub
echo ""
echo "[Step 3/3] Pushing to Docker Hub..."
echo "Note: If not logged in, run 'docker login' first."
docker push "${FULL_IMAGE}"
docker push "${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest"

echo ""
echo "=========================================================="
echo "[SUCCESS] Docker image successfully pushed to Docker Hub!"
echo "URL: https://hub.docker.com/r/${DOCKERHUB_USERNAME}/${IMAGE_NAME}"
echo "Pull command for graders:"
echo "  docker run -it --rm ${FULL_IMAGE}"
echo "=========================================================="
