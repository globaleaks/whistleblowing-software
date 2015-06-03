#!/bin/bash

# user permission check
if [ ! $(id -u) = 0 ]; then
    echo "Error: GlobaLeaks install script must be runned by root"
    exit 1
fi

INSTALL_LOG="./install.log"

PGP_KEY="
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1

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
=J7+v
-----END PGP PUBLIC KEY BLOCK-----"

DISTRO="unknown"
DISTRO_CODENAME="unknown"
if which lsb_release >/dev/null; then
  DISTRO="$( lsb_release -is )"
  DISTRO_CODENAME="$( lsb_release -cs )"
fi

SUPPORTED_PLATFORM=0
if [ "$DISTRO_CODENAME" = "precise" ] ||
   [ "$DISTRO_CODENAME" = "trusty" ] ||
   [ "$DISTRO_CODENAME" = "wheezy" ] ||
   [ "$DISTRO_CODENAME" = "jessie" ]; then
  SUPPORTED_PLATFORM=1
fi

if [ $SUPPORTED_PLATFORM -eq 0 ]; then
  echo "!!!!!!!!!!!! WARNING !!!!!!!!!!!!"
  echo "You are attempting to install GlobaLeaks on an unsupported platform."
  echo "Supported platform are Ubuntu (precise, trusty) and Debian (wheezy, jessie)"

  while true; do
    read -p "Do you wish to continue anyhow? [y|n]?" yn
    case $yn in
      [Yy]*) break;;
      [Nn]*) echo "Installation aborted."; exit;;
      *) echo $yn; echo "Please answer y/n."; continue;;
    esac
  done
fi

echo "Performing GlobaLeaks installation on $DISTRO - $DISTRO_CODENAME"

if [ $SUPPORTED_PLATFORM -eq 0 ]; then
  # In case of unsupported platforms we fallback on trusty
  echo "Given that the platform is not supported the install script will use trusty repository."
  echo "In case of failure refer to the wiki for manual setup possibilities."
  echo "GlobaLeaks Wiki Address: https://github.com/globaleaks/GlobaLeaks/wiki"

  # Given the fact that the platform is not supported be try as it is an Ubuntu 14.04
  DISTRO="Ubuntu"
  DISTRO_CODENAME="trusty"
fi

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
  $CMD &>${INSTALL_LOG}
  if [ "$?" -eq "$2" ]; then
    echo "SUCCESS"
  else
    echo "FAIL"
    echo "COMBINED STDOUT/STDERR OUTPUT OF FAILED COMMAND:"
    cat ${INSTALL_LOG}
    exit 1
  fi
}

# Preliminary Requirements Check
ERR=0
echo "Checking preliminary GlobaLeaks requirements"
for REQ in apt-key apt-get
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

echo "Adding GlobaLeaks PGP key to trusted APT keys"
TMPFILE=/tmp/globaleaks_key.$RANDOM
echo "$PGP_KEY" > $TMPFILE
DO "apt-key add $TMPFILE" "0"
DO "rm -f $TMPFILE" "0"

DO "apt-get update -y" "0"

# on Ubuntu python-pip requires universe repository
if [ $DISTRO == 'Ubuntu' ];then
  if [ "$DISTRO_CODENAME" = "precise" ]; then
    echo "Installing python-software-properties"
    DO "apt-get install python-software-properties -y" "0"
  fi

  if [ "$DISTRO_CODENAME" = "trusty" ]; then
    echo "Installing software-properties-common"
    DO "apt-get install software-properties-common -y" "0"
  fi

  echo "Adding Ubuntu Universe repository"
  add-apt-repository 'deb http://archive.ubuntu.com/ubuntu $(lsb_release -sc) universe'
fi

if [ ! -f /etc/apt/sources.list.d/globaleaks.list ]; then
  # we avoid using apt-add-repository as we prefer using /etc/apt/sources.list.d/globaleaks.list
  echo "deb http://deb.globaleaks.org $DISTRO_CODENAME/" > /etc/apt/sources.list.d/globaleaks.list
fi

DO "apt-get update -y" "0"

DO "apt-get install globaleaks -y" "0"

if [ -r /var/globaleaks/torhs/hostname ]; then
  TORHS=`cat /var/globaleaks/torhs/hostname`
  echo "To access your GlobaLeaks use the following Tor HS URL: $TORHS"
  echo "Use Tor Browser to access it, download it from https://antani.tor2web.org/gettor"
  echo "If you need to access it directly on your public IP address, you must edit /etc/default/globaleaks and restart globaleaks"
fi
