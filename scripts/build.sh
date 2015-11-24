#!/bin/bash

set -e

usage() {
  echo "GlobaLeaks Build Script"
  echo "Valid options:"
  echo " -h"
  echo -e " -t tagname (build specific release/branch)"
  echo -e " -d distribution (available: precise, trusty, wheezy, jessie)"
  echo -e " -n (do not sign)"
}

DISTRIBUTION="trusty"
TAG="master"
NOSIGN=0

while getopts "d:nt:h" opt; do
  case $opt in
    d) DISTRIBUTION="$OPTARG"
    ;;
    t) TAG="$OPTARG"
    ;;
    n) NOSIGN=1
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

if [ "$DISTRIBUTION" != "all" ] &&
   [ "$DISTRIBUTION" != "precise" ] &&
   [ "$DISTRIBUTION" != "trusty" ] &&
   [ "$DISTRIBUTION" != "wheezy" ] &&
   [ "$DISTRIBUTION" != "jessie" ]; then
 usage
 exit 1
fi

if [ "$DISTRIBUTION" == "all" ]; then
  TARGETS="precise trusty wheezy jessie"
else
  TARGETS=$DISTRIBUTION
fi

BUILDSRC="GLRelease"
[ -d $BUILDSRC ] && rm -rf $BUILDSRC
mkdir $BUILDSRC && cd $BUILDSRC
git clone https://github.com/globaleaks/GlobaLeaks.git
cd GlobaLeaks
git checkout $TAG
cd client
npm install grunt-cli
npm install
grunt setupDependencies
grunt build
cd ../../../

for TARGET in $TARGETS; do
  echo "Packaging GlobaLeaks for:" $TARGET

  BUILDDIR="GLRelease-$TARGET"

  [ -d $BUILDDIR ] && rm -rf $BUILDDIR

  cp -r $BUILDSRC $BUILDDIR
  cd $BUILDDIR/GlobaLeaks
  rm debian/control
  ln -s control.$TARGET debian/control
  sed -i "s/stable; urgency=/$TARGET; urgency=/g" debian/changelog

  if [ $NOSIGN -eq 1 ]; then
    debuild -i -us -uc -b
  else
    debuild
  fi

  cd ../../
done
