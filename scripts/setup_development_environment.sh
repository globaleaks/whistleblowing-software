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

DISTRIBUTION=$(lsb_release -c)
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

if [ "$DISTRO" != "Ubuntu" ]; then
 echo "Failure: this script is meant to be used only on Ubuntu"
 exit 1
fi

if [ -d "GlobaLeaks" ]; then
 echo "Failure: found an existing local GlobaLeaks directory"
 exit 1
fi

echo "GlobaLeaks Setup Development Environment Script"

echo "Step 1/8: add universe repository"
sudo apt-get install software-properties-common
sudo add-apt-repository universe

echo "Step 2/8: update"
sudo apt-get update

echo "Step 3/8: apt-get install"
sudo apt-get install build-essential curl git python-pip libssl-dev libffi-dev python-virtualenv python-dev python-sphinx

echo "Step 4/8: git clone"
git clone https://github.com/globaleaks/GlobaLeaks.git
if [ "$TAG" != "master"]; then
  cd GlobaLeaks/ && git checkout $TAG && cd ..
fi

echo "Step 5/8: install npm and node"
curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -
sudo apt-get install -y nodejs

echo "Step 6/8: install grunt"
npm install grunt-cli

echo "Step 7/8: setup client dependencies"
cd GlobaLeaks/client
npm install -d
./node_modules/grunt/bin/grunt copy:sources
cd ../../

echo "Step 8/8: prepare backend virtualenv"
cd GlobaLeaks/backend

rm requirements.txt

cp requirements/requirements-$DISTRO_CODENAME.txt requirements.txt

virtualenv -p python2.7 glenv
source glenv/bin/activate
python setup.py develop --always-unzip 
cd ../../
