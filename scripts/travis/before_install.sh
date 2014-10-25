#!/bin/bash

# setup global variables
# XXX. these are going to be sourced from
# ./scripts/common_inc.sh
# later on.
OWNER="${TRAVIS_REPO_SLUG%/*}"
GLBACKEND_GIT_REPO="https://github.com/$OWNER/GLBackend.git"
GLCLIENT_GIT_REPO="https://github.com/$OWNER/GLClient.git"

TAG="$TRAVIS_BRANCH"

# clone backend and client
git clone $GLBACKEND_GIT_REPO
git clone $GLCLIENT_GIT_REPO

(cd GLBackend/ && \
 git checkout $TAG >& /dev/null || git checkout HEAD >& /dev/null)
(cd GLClient/ && \
 git checkout $TAG >& /dev/null || git checkout HEAD >& /dev/null)


# Add tor repository.
sudo add-apt-repository \
    "deb http://deb.torproject.org/torproject.org $(lsb_release -s -c) main"
gpg --keyserver x-hkp://pool.sks-keyservers.net --recv-keys 0x886DDD89
gpg --export A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89 | sudo apt-key add -

# Add apt repository
sudo add-apt-repository -y ppa:chris-lea/node.js

sudo apt-get update -qq
