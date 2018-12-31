#!/bin/bash -e

# Login on Docker Hub
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

# Push release tag or devel branch
if [ -n "$TRAVIS_TAG" ]; then
  docker tag "$DOCKER_IMAGE_NAME:latest" "$DOCKER_IMAGE_NAME:$TRAVIS_TAG"
  docker push "$DOCKER_IMAGE_NAME:$TRAVIS_TAG"
elif [ "$TRAVIS_BRANCH" == "devel" ]; then
  docker tag "$DOCKER_IMAGE_NAME:latest" "$DOCKER_IMAGE_NAME:$TRAVIS_BRANCH"
  docker push "$DOCKER_IMAGE_NAME:$TRAVIS_BRANCH"
fi
