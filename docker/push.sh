#!/bin/bash -e

# Login on Docker Hub
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

# Always push latest tag when building master
docker push "$DOCKER_IMAGE_NAME:latest"

# Push release tag if current build
if [ -n "$TRAVIS_TAG" ]; then
  docker tag "$DOCKER_IMAGE_NAME:latest" "$DOCKER_IMAGE_NAME:$TRAVIS_TAG"
  docker push "$DOCKER_IMAGE_NAME:$TRAVIS_TAG"
fi
