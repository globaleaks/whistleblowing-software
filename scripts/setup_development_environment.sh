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

DISTRIBUTION=`lsb_release -c`
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

echo "Step 1/9: add universe repository"
if [ "$DISTRO_CODENAME" = "precise" ]; then
  sudo apt-get install python-software-properties -y
else
  sudo apt-get install software-properties-common
fi
sudo add-apt-repository universe

echo "Step 2/9: update"
sudo apt-get update

echo "Step 3/9: apt-get install"
sudo apt-get install build-essential git python-pip libssl-dev libffi-dev python-virtualenv python-dev 

echo "Step 4/9: git clone"
git clone git@github.com:globaleaks/GlobaLeaks.git
if [ "$TAG" != "master"]; then
  cd GlobaLeaks/ && git checkout $TAG && cd ..
fi

echo "Step 5/9: install npm and node"
curl -sL https://deb.nodesource.com/setup_4.x | sudo -E bash -
sudo apt-get install -y nodejs

echo "Step 6/9: install grunt and bower"
sudo npm install -g grunt grunt-cli bower

echo "Step 7/9: setup client dependencies"
cd GlobaLeaks/client
npm install -d
grunt setupDependencies
cd ../../

echo "Step 8/9: prepare backend virtualenv"
cd GlobaLeaks/backend
virtualenv -p python2.7 glenv
source glenv/bin/activate
python setup.py develop --always-unzip 
cd ../../

echo "Step 9/9: finally start  globaleaks"
./GlobaLeaks/backend/bin/globaleaks -z -d -n
