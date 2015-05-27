#!/bin/bash

set -e

die() {
  echo "Please specify a valid distro codename"
  echo "Available: precise, trusty, wheezy, jessie";
  echo "e.g.: $0 precise"
  exit 1;
}

DISTRIBUTION="precise"
NOSIGN=0

while getopts "d:n" opt; do
  case $opt in
    d) DISTRIBUTION="$OPTARG"
    ;;
    n) NOSIGN=1
    ;;
    \?) echo "Invalid option -$OPTARG" >&2
        die
    ;;
  esac
done

if [ "$DISTRIBUTION" != "precise" ] &&
   [ "$DISTRIBUTION" != "trusty" ] &&
   [ "$DISTRIBUTION" != "wheezy" ] &&
   [ "$DISTRIBUTION" != "jessie" ]; then
 die
fi

echo "Packaging GlobaLeaks for:" $DISTRIBUTION

[ -d GLRelease ] && rm -rf GLRelease

mkdir GLRelease
cd GLRelease
git clone git@github.com:globaleaks/GlobaLeaks.git
cd GlobaLeaks
rm debian/control
ln -s control.$DISTRIBUTION debian/control
sed -i "s/UNRELEASED/$DISTRIBUTION/g" debian/changelog

if [ $NOSIGN -eq 1 ]; then
  debuild -i -us -uc -b
else
  debuild
fi
