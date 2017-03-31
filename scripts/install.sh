#!/bin/bash

# user permission check
if [ ! $(id -u) = 0 ]; then
    echo "Error: GlobaLeaks install script must be run by root"
    exit 1
fi

ASSUMEYES=0
EXPERIMENTAL=0
for arg in "$@"; do
  shift
  case "$arg" in
    --assume-yes ) ASSUMEYES=1; shift ;;
    --install-experimental-version-and-accept-the-consequences ) EXPERIMENTAL=1; shift ;;
    -- ) shift; break ;;
    * ) break ;;
  esac
done

if [ $EXPERIMENTAL -eq 1 ]; then
  echo "!!!!!!!!!!!! WARNING !!!!!!!!!!!!"
  echo "You requested to install the experimental version."
  echo "This version is currently under peer review and MUST NOT be used in production."
fi

LOGFILE="./install.log"

DISTRO="unknown"
DISTRO_CODENAME="unknown"
if which lsb_release >/dev/null; then
  DISTRO="$( lsb_release -is )"
  DISTRO_CODENAME="$( lsb_release -cs )"
fi

echo "Detected OS: $DISTRO - $DISTRO_CODENAME"

if echo "$DISTRO_CODENAME" | grep -vqE "^xenial$" ; then
  echo "WARNING: The up-to-date required platform is Ubuntu Xenial (16.04)"

  if [ $ASSUMEYES -eq 0 ]; then
    while true; do
      read -p "Do you wish to continue anyway? [y|n]?" yn
      case $yn in
        [Yy]*) break;;
        [Nn]*) echo "Installation aborted."; exit;;
        *) echo $yn; echo "Please answer y/n."; continue;;
      esac
    done
  fi
fi

# The supported platforms are experimentally more than only Ubuntu as
# publicly communicated to users.
#
# Depending on the intention of the user to proceed anyhow installing on
# a not supported distro we using the experimental package if it exists
# or xenial as fallback.
if echo "$DISTRO_CODENAME" | grep -vqE "^(precise|trusty|xenial|wheezy|jessie)$" ; then
  # In case of unsupported platforms we fallback on Trusty
  echo "No packages available for the current distribution; the install script will use the xenial repository."
  echo "In case of a failure refer to the wiki for manual setup possibilities."
  echo "GlobaLeaks Wiki: https://github.com/globaleaks/GlobaLeaks/wiki"
  DISTRO="Ubuntu"
  DISTRO_CODENAME="xenial"
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
  $CMD &>${LOGFILE}
  if [ "$?" -eq "$RET" ]; then
    echo "SUCCESS"
  else
    echo "FAIL"
    echo "COMBINED STDOUT/STDERR OUTPUT OF FAILED COMMAND:"
    cat ${LOGFILE}
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
DO "wget https://deb.globaleaks.org/globaleaks.asc -O $TMPFILE"
DO "apt-key add $TMPFILE"
DO "rm -f $TMPFILE"

DO "apt-get update -y"

# on Ubuntu python-pip requires universe repository
if [ $DISTRO == "Ubuntu" ]; then
  if [ $DISTRO_CODENAME == "precise" ]; then
    echo "Installing python-software-properties"
    DO "apt-get install python-software-properties -y"
  else
    echo "Installing software-properties-common"
    DO "apt-get install software-properties-common -y"
  fi

  echo "Adding Ubuntu Universe repository"
  add-apt-repository "deb http://archive.ubuntu.com/ubuntu $(lsb_release -sc) universe"
fi

if [ -d /data/globaleaks/deb ]; then
  DO "apt-get update -y"
  DO "apt-get install dpkg-dev -y"
  echo "Installing from locally provided debian package"
  cd /data/globaleaks/deb/ && dpkg-scanpackages . /dev/null | gzip -c -9 > /data/globaleaks/deb/Packages.gz
  echo "deb file:///data/globaleaks/deb/ /" >> /etc/apt/sources.list
  # must update the cache after the package has been added
  DO "apt-get update -y"
  DO "apt-get install globaleaks -y --force-yes -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confnew"
else
  if [ ! -f /etc/apt/sources.list.d/globaleaks.list ]; then
    # we avoid using apt-add-repository as we prefer using /etc/apt/sources.list.d/globaleaks.list
    if [ $EXPERIMENTAL -eq 0 ]; then
      echo "deb http://deb.globaleaks.org $DISTRO_CODENAME/" > /etc/apt/sources.list.d/globaleaks.list
    else
      echo "deb http://deb.globaleaks.org unstable/" > /etc/apt/sources.list.d/globaleaks.list
    fi
  fi
  DO "apt-get update -y"
  DO "apt-get install globaleaks -y"
fi

#TODO this is timing dependent
echo "Waiting for onion service to configure"
sleep 60
if [ -r /var/run/globaleaks/globaleaks.pid ]; then
  TORHS=`gl-admin readvar --varname=tor_onion_hostname`
  echo "To access and configure your GlobaLeaks node use the following Tor HS URL: $TORHS"
  echo "Use the Tor Browser to connect, You can download it from https://www.torproject.org/download"
  echo "If you need to access the node directly on your public IP address, edit /etc/default/globaleaks and restart globaleaks"
fi
