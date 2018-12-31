#!/bin/bash -e

# Build image
docker build -t "$DOCKER_IMAGE_NAME:latest" .

# Run container on background
CONTAINER_ID=$(docker run --rm -d -p '8080:80' -p '443:443' "$DOCKER_IMAGE_NAME:latest")

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
