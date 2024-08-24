#!/bin/bash
set -e

DEBIAN_TARGET='bookworm'

build_publish_image() {

	IMAGE_NAME='globaleaks/globaleaks'

	GIT_TAG="$1"

	cd "$GITHUB_WORKSPACE"/docker/;

	echo "building docker image ..."
	
	docker build -t "$IMAGE_NAME":"$GIT_TAG" .

	docker tag "$IMAGE_NAME":"$GIT_TAG" "IMAGE_NAME":latest
	
	echo "pushing image to the docker hub ..."
	
	docker login -u globaleaks -p "$DOCKER_HUB_TOKEN"
	
	docker push "$IMAGE_NAME":"$GIT_TAG"

	docker push "$IMAGE_NAME":latest
}

DEB_RELEASES=$(curl -s https://deb.globaleaks.org/"$DEBIAN_TARGET"/Packages | awk '/^Version: / {print $2}' | xargs)

echo "Available GlobaLeaks releases: $DEB_RELEASES"
echo "Github Tag: ${GITHUB_REF_NAME:1}"

# if the github GITHUB_REF_NAME matches any one of the debian version, proceeds to build the image
if echo "$DEB_RELEASES" | grep -qw "${GITHUB_REF_NAME:1}"; then
    echo "Match found!"
		build_publish_image "$GITHUB_REF_NAME"
		exit
else
	echo "No match found :("
		exit 1
fi
