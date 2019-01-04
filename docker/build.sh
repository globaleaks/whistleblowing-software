#!/bin/bash -e

DOCKER_IMAGE_NAME=globaleaks/globaleaks

if [ -z ${DOCKER_IMAGE_TAG+x} ]; then
  DOCKER_IMAGE_TAG=latest
fi

# Build image
docker build -t "$DOCKER_IMAGE_NAME:$DOCKER_IMAGE_TAG" .

# Run container on background
CONTAINER_ID=$(docker run --rm -d -p '8080:80' -p '443:443' "$DOCKER_IMAGE_NAME:$DOCKER_IMAGE_TAG")

# Wait for server ready
retry=0
while ! curl -sS -I localhost:8080; do
  retry=$((retry + 1))
  if [ $retry -eq 10 ]; then
    echo 'Unable to reach container port'
    exit 1
  fi
  sleep 1;
done

# Expect html page
curl -sS --compressed localhost:8080 | grep 'start_globaleaks'

# Cleanup
docker rm -f "$CONTAINER_ID"
