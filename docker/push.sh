#!/bin/bash -e

DOCKER_IMAGE_NAME=globaleaks/globaleaks

if [ -z ${DOCKER_IMAGE_TAG+x} ]; then
  DOCKER_IMAGE_TAG=latest
fi

# Login on Docker Hub
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

docker push "$DOCKER_IMAGE_NAME:$DOCKER_IMAGE_TAG"
