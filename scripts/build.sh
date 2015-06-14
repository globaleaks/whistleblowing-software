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

DISTRIBUTION="precise"
TAG="master"
NOSIGN=0

while getopts "d:n:th" opt; do
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

if [ "$DISTRIBUTION" != "precise" ] &&
   [ "$DISTRIBUTION" != "trusty" ] &&
   [ "$DISTRIBUTION" != "wheezy" ] &&
   [ "$DISTRIBUTION" != "jessie" ]; then
 usage
 exit 1
fi

echo "Packaging GlobaLeaks for:" $DISTRIBUTION

[ -d GLRelease ] && rm -rf GLRelease

mkdir GLRelease
cd GLRelease
git clone git@github.com:globaleaks/GlobaLeaks.git
cd GlobaLeaks
git checkout $TAG
rm debian/control
ln -s control.$DISTRIBUTION debian/control
sed -i "s/stable; urgency=/$DISTRIBUTION; urgency=/g" debian/changelog

if [ $NOSIGN -eq 1 ]; then
  debuild -i -us -uc -b
else
  debuild
fi
