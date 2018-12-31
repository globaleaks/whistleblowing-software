#!/bin/bash -e
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
docker push globaleaks/globaleaks:latest
docker tag globaleaks/globaleaks:latest globaleaks/globaleaks:$TRAVIS_BUILD_NUMBER
docker push globaleaks/globaleaks:$TRAVIS_BUILD_NUMBER
