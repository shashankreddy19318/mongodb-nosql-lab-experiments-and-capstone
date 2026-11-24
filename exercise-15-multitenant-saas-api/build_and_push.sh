#!/usr/bin/env bash
set -e

USERNAME=${1:-"shashankreddy30"}
IMAGE="mongodb-lab15"
TAG=${2:-"latest"}
FULL_IMAGE="$USERNAME/$IMAGE:$TAG"

echo "=========================================================="
echo "  Building and Pushing Lab 15 Multi-Tenant SaaS Demo Image"
echo "  Target Image: $FULL_IMAGE"
echo "  Docker Hub:   https://hub.docker.com/r/$USERNAME/$IMAGE"
echo "=========================================================="

docker build -t "$FULL_IMAGE" -t "$USERNAME/$IMAGE:latest" -t "shashankreddy30/nosql-lab15:latest" -t "chintan/$IMAGE:latest" -t "$IMAGE:latest" .
docker push "$FULL_IMAGE"
docker push "shashankreddy30/nosql-lab15:latest"

echo "=========================================================="
echo "[SUCCESS] Image successfully published to Docker Hub!"
echo "Docker Hub URL: https://hub.docker.com/r/$USERNAME/$IMAGE"
echo "Demonstration:  docker run --rm -it $FULL_IMAGE demo"
echo "Live Server:    docker run --rm -it -p 8000:8000 $FULL_IMAGE server"
echo "=========================================================="
