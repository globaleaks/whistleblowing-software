#!/bin/bash

# user permission check
if [ ! $(id -u) = 0 ]; then
    echo "Error: GlobaLeaks install script must be runned by root"
    exit 1
fi

EXPERIMENTAL=1
for arg in "$@"; do
  shift
  case "$arg" in
    --install-experimental-version-and-accept-the-consequences ) EXPERIMENTAL=0; shift ;;
    -- ) shift; break ;;
    * ) break ;;
  esac
done

if [ $EXPERIMENTAL -eq 0 ]; then
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

SUPPORTED_PLATFORM=0
if [ "$DISTRO_CODENAME" = "precise" ] ||
   [ "$DISTRO_CODENAME" = "trusty" ]; then
  SUPPORTED_PLATFORM=1
fi

if [ $SUPPORTED_PLATFORM -eq 0 ]; then
  echo "!!!!!!!!!!!! WARNING !!!!!!!!!!!!"
  echo "You are attempting to install GlobaLeaks on an unsupported platform."
  echo "Supported platform is Ubuntu (precise, trusty)"

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

# The supported platforms are experimentally more than only Ubuntu as
# publicly communicated to users.
#
# Depending on the intention of the user to proceed anyhow installing on
# a not supported distro we using the experimental package if it exists
# or trusty as fallback.
if [ "$DISTRO_CODENAME" != "precise" ] &&
   [ "$DISTRO_CODENAME" != "trusty" ] &&
   [ "$DISTRO_CODENAME" != "wheezy" ] &&
   [ "$DISTRO_CODENAME" != "jessie" ]; then
  # In case of unsupported platforms we fallback on Trusty
  echo "Given that the platform is not supported the install script will use trusty repository."
  echo "In case of failure refer to the wiki for manual setup possibilities."
  echo "GlobaLeaks Wiki Address: https://github.com/globaleaks/GlobaLeaks/wiki"
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
if [ $DISTRO == 'Ubuntu' ]; then
  if [ "$DISTRO_CODENAME" = "precise" ]; then
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
  cd /data/globaleaks/deb/ && dpkg-scanpackages . /dev/null | gzip -c -9 > /data/globaleaks/deb/Packages.gz
  echo 'deb file:///data/globaleaks/deb/ /' >> /etc/apt/sources.list
  DO "apt-get update -y"
  DO "apt-get install dpkg-dev -y"
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

if [ -r /var/globaleaks/torhs/hostname ]; then
  TORHS=`cat /var/globaleaks/torhs/hostname`
  echo "To access your GlobaLeaks use the following Tor HS URL: $TORHS"
  echo "Use Tor Browser to access it, download it from https://antani.tor2web.org/gettor"
  echo "If you need to access it directly on your public IP address, you must edit /etc/default/globaleaks and restart globaleaks"
fi
