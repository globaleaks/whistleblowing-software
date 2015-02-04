#!/bin/sh

# user permission check
if [ ! $(id -u) = 0 ]; then
    echo "Error: GlobaLeaks install script must be runned by root"
    exit 1
fi

DISTRO='unknown'
DISTRO_VERSION='unknown'
SUPPORTED_PLATFORM=0

if [ -r /lib/lsb/init-functions ]; then
  if [ "$( lsb_release -is )" = "Debian" ]; then
    DISTRO="debian"
    DISTRO_VERSION="$( lsb_release -cs )"
  else
    DISTRO="ubuntu"
    DISTRO_VERSION="$( lsb_release -cs )"
  fi
fi

if [ $DISTRO = "debian" ]; then
  if [ $DISTRO_VERSION = "wheezy" ] || [ $DISTRO_VERSION = "jessie" ]; then
    SUPPORTED_PLATFORM=1
  fi
elif [ $DISTRO = "ubuntu" ]; then
  if [ $DISTRO_VERSION = "precise" || $DISTRO_VERSION = "trusty" ]; then
    SUPPORTED_PLATFORM=1
  fi
fi

if [ $SUPPORTED_PLATFORM -eq 0 ]; then
  echo "!!!!!!!!!!!! WARNING !!!!!!!!!!!!"
  echo "You are attempting to install GlobaLeaks on an unsupported platform."
  echo "Supported platform are Debian (wheezy, jessie) and Ubuntu (precise, trusty)\n"
  echo "Do you wish to continue at your own risk [Y|N]? "
  read ans
  if [ $ans = y -o $ans = Y -o $ans = yes -o $ans = Yes -o $ans = YES ]
  then
    echo "Ok, you wanted it!\n"
  else
    echo "Installation aborted. Still friends, right?"
    exit
  fi
fi

echo "Performing GlobaLeaks installation on $DISTRO - $DISTRO_VERSION"

DO () {
  if [ -z "$2" ]; then
    RET=0
  else
    RET=$2
  fi
  if [ -z "$3" ]; then
    CMD=$1
  else
    CMD=$3
  fi
  echo -n "Running: \"$CMD\"... "
  $1 &>${BUILD_LOG}
  if [ "$?" -eq "$2" ]; then
    echo "SUCCESS"
  else
    echo "FAIL"
    echo "COMBINED STDOUT/STDERR OUTPUT OF FAILED COMMAND:"
    cat ${BUILD_LOG}
    exit 1
  fi
}

if [ ! -f /etc/apt/sources.list.d/globaleaks ]; then
    echo "deb http://deb.globaleaks.org $DISTRO_VERSION/" > /etc/apt/sources.list.d/globaleaks.list
fi

# Preliminary Requirements Check
ERR=0
echo "Checking preliminary GlobaLeaks requirements"
for REQ in apt-key apt-get gpg
do
  if which $REQ >/dev/null; then
    echo " + $REQ requirement meet"
  else
    ERR=$(($ERR+1))
    echo " - $REQ requirement not meet"
  fi
done

if [ $ERR -ne 0 ]; then
  echo "Error: Found ${ERR} unmet requirements"
  exit 1
fi

gpg --keyserver keys.gnupg.net --recv-keys B353922AE4457748559E777832E6792624045008
gpg --export B353922AE4457748559E777832E6792624045008 | apt-key add -

DO "apt-get update -y" "0"
DO "apt-get install globaleaks -y" "0"
