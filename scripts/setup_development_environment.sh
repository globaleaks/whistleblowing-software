#!/bin/bash

# This script enable to setup the globaleaks development environment
# 
# The status of the installation process is printed to the console and
# saved in the local file setup_log.txt.
#
# The script is intended to work on Ubuntu where:
# - some commands need to be executed with root privileges and are prefixed with sudo
# - some commands need to be excecuted with the developer user.

# this force to exit at first error returned
set -e

TAG="master"

# Redirect stdout ( > ) into a named pipe ( >() ) running "tee"
exec > >(tee -i ./setup_log.txt)

usage() {
  echo "GlobaLeaks Setup Development Environment Script (Ubuntu only)"
  echo "Valid options:"
  echo " -h"
  echo -e " -t tagname (prepare for development on specific release/branch)"
}

while getopts "t:h" opt; do
  case $opt in
    t) TAG="$OPTARG"
    ;;
    h)
        usage
        exit 1
    ;;
    \?) usage
        exit 1
    ;;
  esac
done

DISTRO="unknown"
DISTRO_CODENAME="unknown"
if which lsb_release >/dev/null; then
  DISTRO="$( lsb_release -is )"
  DISTRO_CODENAME="$( lsb_release -cs )"
fi

if echo "$DISTRO" | grep -vqE "^(Debian|Ubuntu)$"; then
 echo "Failure: this script is meant to be used only on Debian and Ubuntu"
 exit 1
fi

if [ -d "GlobaLeaks" ]; then
 echo "Failure: found an existing local GlobaLeaks directory"
 exit 1
fi

echo "GlobaLeaks Setup Development Environment Script"

sudo apt-get update
sudo apt-get install curl dh-apparmor debhelper devscripts dput git libssl-dev python3-dev python3-pip python3-setuptools python3-sphinx python3-venv

git clone https://github.com/globaleaks/GlobaLeaks.git
if [ "$TAG" != "master"]; then
  cd GlobaLeaks/ && git checkout $TAG && cd ..
fi

curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash -
sudo apt-get install -y nodejs

cd GlobaLeaks/client
npm install -d
./node_modules/grunt/bin/grunt copy:sources
cd ../../

cd GlobaLeaks/backend
rm requirements.txt
cp requirements/requirements-$DISTRO_CODENAME.txt requirements.txt

python3 -mvenv env
source env/bin/activate
python setup.py develop --always-unzip 
cd ../../
