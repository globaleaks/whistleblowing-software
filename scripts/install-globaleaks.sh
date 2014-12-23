#!/bin/sh

# if the distro version is not recognized precise is used
DISTRO_VERSION="$( lsb_release -cs )"
case ${DISTRO_VERSION} in
    precise|trusty|wheezy|jessie);;
    *) DISTRO_VERSION='precise';;
esac

if ! $(grep -q globaleaks /etc/apt/sources.list); then
  echo "deb http://deb.globaleaks.org $DISTRO_VERSION/" > /etc/apt/sources.list
fi

gpg --recv-keys --armor 24045008
gpg --export --armor 24045008 | apt-key add -

apt-get update
apt-get install globaleaks
