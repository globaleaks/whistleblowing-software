#!/bin/bash

set -e

DISTRIBUTION="trusty"
TAG="master"
NOSIGN=0

usage() {
  echo "GlobaLeaks Build Script"
  echo "Valid options:"
  echo " -h"
  echo -e " -t tagname (build specific release/branch)"
  echo -e " -l (Use local repository & enviroment)"
  echo -e " -d distribution (available: trusty, xenial, wheezy, jessie)"
  echo -e " -n (do not sign)"
  echo -e " -p (push on repository)"
}

TARGETS="trusty xenial wheezy jessie"
DISTRIBUTION="trusty"
TAG="master"
LOCAL_ENV=0
NOSIGN=0
PUSH=0

while getopts "d:t:np:h:l" opt; do
  case $opt in
    d) DISTRIBUTION="$OPTARG"
    ;;
    t) TAG="$OPTARG"
    ;;
    n) NOSIGN=1
    ;;
    p) PUSH=1
    ;;
    l) LOCAL_ENV=1
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

if ! [[ $TARGETS =~ $DISTRIBUTION ]] && [[ $DISTRIBUTION != 'all' ]]; then
 usage
 exit 1
fi

if [ "$DISTRIBUTION" != 'all' ]; then
  TARGETS=$DISTRIBUTION
fi

# Preliminary Requirements Check
ERR=0
echo "Checking preliminary GlobaLeaks Build requirements"
for REQ in git npm debuild dput
do
  if which $REQ >/dev/null; then
    echo " + $REQ requirement meet"
  else
    ERR=$((ERR+1))
    echo " - $REQ requirement not meet"
  fi
done

if [ $ERR -ne 0 ]; then
  echo "Error: Found ${ERR} unmet requirements"
  echo "Information on how to setup globaleaks development environment at: https://github.com/globaleaks/GlobaLeaks/wiki/setting-up-globaleaks-development-environment"
  exit 1
fi

ROOTDIR=$(pwd)

BUILDSRC="GLRelease"
[ -d $BUILDSRC ] && rm -rf $BUILDSRC
mkdir $BUILDSRC && cd $BUILDSRC

if [ $LOCAL_ENV -eq 1 ]; then
  cd ../client/
  ./node_modules/grunt/bin/grunt build
  cd ../GLRelease
  git clone --branch="$TAG" --depth=1 file://$(pwd)/../../GlobaLeaks
  cp -rf ../client/build GlobaLeaks/client/
else
  git clone https://github.com/globaleaks/GlobaLeaks.git
  cd GlobaLeaks
  git checkout $TAG
  cd client
  npm install
  ./node_modules/grunt/bin/grunt build
fi

cd $ROOTDIR

for TARGET in $TARGETS; do
  echo "Packaging GlobaLeaks for:" $TARGET

  BUILDDIR="GLRelease-$TARGET"

  [ -d $BUILDDIR ] && rm -rf $BUILDDIR

  cp -r $BUILDSRC $BUILDDIR
  cd $BUILDDIR/GlobaLeaks

  rm debian/control backend/requirements.txt

  cp debian/controlX/control.$TARGET  debian/control
  cp backend/requirements/requirements-$TARGET.txt backend/requirements.txt

  sed -i "s/stable; urgency=/$TARGET; urgency=/g" debian/changelog

  if [ $NOSIGN -eq 1 ]; then
    debuild -i -us -uc -b
  else
    debuild
  fi

  cd ../../
done

if [ $PUSH -eq 1 ]; then
  for TARGET in $TARGETS; do

    BUILDDIR="GLRelease-$TARGET"

    cp -r $BUILDSRC $BUILDDIR

    dput globaleaks globaleaks*changes

    cd ../../
  done
fi
