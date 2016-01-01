#!/bin/bash

set -e

usage() {
  echo "GlobaLeaks Packer Script"
  echo "Valid options:"
  echo " -h"
  echo -e " -d distribution (available: precise, trusty, wheezy, jessie)"
}

pushd `dirname $0` > /dev/null
SCRIPT_PATH=`pwd`
popd > /dev/null

export PACKER_PATH=${SCRIPT_PATH}/packer
export PACKER_CACHE_DIR=${SCRIPT_PATH}/.packer_cache
export PACKER_TEMPLATE=${SCRIPT_PATH}/templates/ubuntu-stable

TEMPLATES="ubuntu-12.04 ubuntu-14.04 ubuntu-16.04 debian-7 debian-8 debian-9"
DISTRIBUTION="ubuntu-14.04"

while getopts "d:nt:h" opt; do
  case $opt in
    d) DISTRIBUTION="$OPTARG"
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

if ! [[ $TEMPLATES =~ $DISTRIBUTION ]] && [[ $DISTRIBUTION != 'all' ]]; then
 usage
 exit 1
fi

if [ "$DISTRIBUTION" == 'all' ]; then
  TARGETS=$TEMPLATES
else
  TARGETS=$DISTRIBUTION
fi

echo "Starting GlobaLeaks packers scripts for the following distributions:" $TARGETS

if ! which virtualbox >/dev/null; then
    echo "Virtualbox requirement is not met."
    echo "Download and install Virtualbox for Linux from: https://www.virtualbox.org/wiki/Linux_Downloads"
    exit 1
fi

if [ ! -d "$PACKER_PATH" ]; then
  mkdir ${PACKER_PATH}
  cd ${PACKER_PATH}
  wget https://releases.hashicorp.com/packer/0.8.6/packer_0.8.6_linux_amd64.zip
  unzip *.zip
fi

export PATH=$PATH:${PACKER_PATH}

for TARGET in $TARGETS; do
  echo "Running GlobaLeaks packer script for:" $TARGET
  cd ${SCRIPT_PATH}/templates/$TARGET
  packer build template.json
  cd ../../..
done
