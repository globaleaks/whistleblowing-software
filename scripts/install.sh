#!/bin/bash

# User Permission Check
if [ ! $(id -u) = 0 ]; then
  echo "Error: GlobaLeaks install script must be run by root"
  exit 1
fi

# Preliminary requirements check
ERR=0
echo "Checking preliminary GlobaLeaks requirements"
for REQ in apt-key apt-get gpg curl
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

DO () {
  if [ -z "$2" ]; then
    EXPECTED_RET=0
  else
    EXPECTED_RET=$2
  fi
  if [ -z "$3" ]; then
    CMD=$1
  else
    CMD=$3
  fi
  echo -n "Running: \"$CMD\"... "
  eval $CMD &>${LOGFILE}

  STATUS=$?

  echo $CMD > $TMPDIR/last_command
  echo $STATUS > $TMPDIR/last_status

  if [ "$STATUS" -eq "$EXPECTED_RET" ]; then
    echo "SUCCESS"
  else
    echo "FAIL"
    echo "COMBINED STDOUT/STDERR OUTPUT OF FAILED COMMAND:"
    cat ${LOGFILE}
    echo "Ouch! The installation failed.\nPlease help us out and report the failure on the forum so that others don't have the same issue. https://forum.globaleaks.org"
    exit 1
  fi
}

LOGFILE="./install.log"
ASSUMEYES=0
EXPERIMENTAL=0
TEST=0

DISTRO="unknown"
DISTRO_CODENAME="unknown"
if which lsb_release >/dev/null; then
  DISTRO="$(lsb_release -is)"
  DISTRO_CODENAME="$(lsb_release -cs)"
fi

# Report last executed command and its status
TMPDIR=`mktemp -d`
echo '' > $TMPDIR/last_command
echo '' > $TMPDIR/last_status

function atexit {
  if [ $TEST -eq 1 ]; then
    DISTRO_CODENAME="test-$DISTRO_CODENAME"
  fi

  LAST_COMMAND=$(cat $TMPDIR/last_command)
  LAST_STATUS=$(cat $TMPDIR/last_status)

  curl -G -m 10 \
       --data-urlencode "DISTRO=$DISTRO_CODENAME"
       --data-urlencode "LAST_COMMAND=$LAST_COMMAND"
       --data-urlencode "LAST_STATUS=$LAST_STATUS"
       "https://deb.globaleaks.org/install-globaleaks.sh" 2>&1

  rm  -r $TMPDIR
}
trap atexit EXIT

for arg in "$@"; do
  shift
  case "$arg" in
    --assume-yes ) ASSUMEYES=1; shift ;;
    --install-experimental-version-and-accept-the-consequences ) EXPERIMENTAL=1; shift ;;
    --test) TEST=1; shift;;
    -- ) shift; break ;;
    * ) break ;;
  esac
done

if [ $EXPERIMENTAL -eq 1 ]; then
  echo "!!!!!!!!!!!! WARNING !!!!!!!!!!!!"
  echo "You requested to install the experimental version."
  echo "This version is currently under peer review and MUST NOT be used in production."
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
if echo "$DISTRO_CODENAME" | grep -vqE "^(trusty|xenial|wheezy|jessie)$"; then
  # In case of unsupported platforms we fallback on Trusty
  echo "No packages available for the current distribution; the install script will use the xenial repository."
  echo "In case of a failure refer to the wiki for manual setup possibilities."
  echo "GlobaLeaks Wiki: https://github.com/globaleaks/GlobaLeaks/wiki"
  DISTRO="Ubuntu"
  DISTRO_CODENAME="xenial"
fi

echo "Adding GlobaLeaks PGP key to trusted APT keys"
TMPFILE=$TMPDIR/globaleaks_key
DO "curl https://deb.globaleaks.org/globaleaks.asc -o $TMPFILE"
DO "apt-key add $TMPFILE"

echo "Adding Tor PGP key to trusted APT"
TMPFILE=$TMPDIR/torproject_key
DO "gpg --keyserver keys.gnupg.net --recv A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89"
DO "gpg --output $TMPFILE --export A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89"
DO "apt-key add $TMPFILE"

DO "apt-get update -y"

if echo "$DISTRO_CODENAME" | grep -qE "^(wheezy)$"; then
  echo "Installing python-software-properties"
  DO "apt-get install python-software-properties -y"
else
  echo "Installing software-properties-common"
  DO "apt-get install software-properties-common -y"
fi

if ! grep -q "^deb .*universe" /etc/apt/sources.list /etc/apt/sources.list.d/*; then
  echo "Adding Ubuntu Universe repository"
  DO "add-apt-repository 'deb http://archive.ubuntu.com/ubuntu $(lsb_release -sc) universe'"
fi

if ! grep -q "^deb .*torproject" /etc/apt/sources.list /etc/apt/sources.list.d/*; then
  echo "Adding Tor repository"
  DO "add-apt-repository 'deb http://deb.torproject.org/torproject.org $(lsb_release -sc) main'"
fi

if [ -d /globaleaks/deb ]; then
  DO "apt-get update -y"
  DO "apt-get install dpkg-dev -y"
  echo "Installing from locally provided debian package"
  cd /globaleaks/deb/ && dpkg-scanpackages . /dev/null | gzip -c -9 > /globaleaks/deb/Packages.gz
  if [ ! -f /etc/apt/sources.list.d/globaleaks.local.list ]; then
    echo "deb file:///globaleaks/deb/ /" >> /etc/apt/sources.list.d/globaleaks.local.list
  fi
  DO "apt-get update -y"
  DO "apt-get install globaleaks -y --allow-unauthenticated -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confnew"
else
  if [ ! -f /etc/apt/sources.list.d/globaleaks.list ]; then
    if [ $EXPERIMENTAL -eq 0 ]; then
      echo "deb http://deb.globaleaks.org $DISTRO_CODENAME/" > /etc/apt/sources.list.d/globaleaks.list
    else
      echo "deb http://deb.globaleaks.org unstable/" > /etc/apt/sources.list.d/globaleaks.list
    fi
  fi
  DO "apt-get update -y"
  DO "apt-get install globaleaks -y"
fi

echo "Install script completed."
echo "GlobaLeaks should be reachable at http://127.0.0.1:8082"
