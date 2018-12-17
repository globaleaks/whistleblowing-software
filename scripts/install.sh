#!/bin/bash

# User Permission Check
if [ ! $(id -u) = 0 ]; then
  echo "Error: GlobaLeaks install script must be run by root"
  exit 1
fi

# Preliminary requirements check
ERR=0
echo "Checking preliminary packaging GlobaLeaks requirements"
for REQ in apt-key apt-get gpg
do
  if which $REQ >/dev/null; then
    echo " + $REQ requirement met"
  else
    ERR=$((ERR+1))
    echo " - $REQ requirement not met"
  fi
done

if [ $ERR -ne 0 ]; then
  echo "Error: Found ${ERR} unmet requirements"
  exit 1
fi

function DO () {
  CMD="$1"

  if [ -z "$2" ]; then
    EXPECTED_RET=0
  else
    EXPECTED_RET=$2
  fi

  echo -n "Running: \"$CMD\"... "
  eval $CMD &>${LOGFILE}

  STATUS=$?

  last_command $CMD
  last_status $STATUS

  if [ "$STATUS" -eq "$EXPECTED_RET" ]; then
    echo "SUCCESS"
  else
    echo "FAIL"
    echo "Ouch! The installation failed."
    echo "COMBINED STDOUT/STDERR OUTPUT OF FAILED COMMAND:"
    cat ${LOGFILE}
    exit 1
  fi
}

LOGFILE="./install.log"
ASSUMEYES=0
EXPERIMENTAL=0
TEST=0

GLOBALEAKS_PGP_KEY="
-----BEGIN PGP PUBLIC KEY BLOCK-----

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
=VudL
-----END PGP PUBLIC KEY BLOCK-----"

DISTRO="unknown"
DISTRO_CODENAME="unknown"
if which lsb_release >/dev/null; then
  DISTRO="$(lsb_release -is)"
  DISTRO_CODENAME="$(lsb_release -cs)"
  REAL_DISTRO=$DISTRO
  REAL_DISTRO_CODENAME=$DISTRO_CODENAME
fi

# LinuxMint is based on Ubuntu, if we encounter Mint just allign the Ubuntu version is based upon
if [ "$DISTRO" == "LinuxMint" ]; then
  DISTRO="Ubuntu"
  DISTRO_CODENAME=$(grep UBUNTU_CODENAME /etc/os-release | sed -e 's/UBUNTU_CODENAME=//')
fi

# Report last executed command and its status
TMPDIR=$(mktemp -d)
echo '' > $TMPDIR/last_command
echo '' > $TMPDIR/last_status

function last_command () {
  echo $1 > $TMPDIR/last_command
}

function last_status () {
  echo $1 > $TMPDIR/last_status
}

function prompt_for_continuation () {
  if [ $ASSUMEYES -eq 0 ]; then
    while true; do
      read -p "Do you wish to continue anyway? [y|n]?" yn
      case $yn in
        [Yy]*) break;;
        [Nn]*) exit 1;;
        *) echo $yn; echo "Please answer y/n.";  continue;;
      esac
    done
  fi
}

function atexit {
  echo "For Professional Support requests please visit: https://www.globaleaks.org/contact/"
  echo "Please report encountered issues to the Community Forum at https://forum.globaleaks.org"

  if [ $TEST -eq 1 ]; then
    REAL_DISTRO_CODENAME="test-$REAL_DISTRO_CODENAME"
  fi

  LAST_COMMAND=$(cat $TMPDIR/last_command)
  LAST_STATUS=$(cat $TMPDIR/last_status)

  curl "https://deb.globaleaks.org/install-globaleaks.sh" \
       -G -m 10 \
       --data-urlencode "DISTRO=$REAL_DISTRO_CODENAME" \
       --data-urlencode "LAST_COMMAND=$LAST_COMMAND" \
       --data-urlencode "LAST_STATUS=$LAST_STATUS" \
       >/dev/null 2>/dev/null

  rm  -r $TMPDIR
}

trap atexit EXIT

for arg in "$@"; do
  shift
  case "$arg" in
    --assume-yes ) ASSUMEYES=1; shift;;
    --install-experimental-version-and-accept-the-consequences ) EXPERIMENTAL=1; shift;;
    --test) TEST=1; shift;;
    -- ) shift; break;;
    * ) break;;
  esac
done

if [ $EXPERIMENTAL -eq 1 ]; then
  echo "!!!!!!!!!!!! WARNING !!!!!!!!!!!!"
  echo "You requested to install the experimental version."
  echo "This version is currently under peer review and MUST NOT be used in production."
fi

echo "Detected OS: $DISTRO - $DISTRO_CODENAME"

last_command "check_distro"

if echo "$DISTRO_CODENAME" | grep -vqE "^bionic$" ; then
  echo "WARNING: GlobaLeaks is actively developed and tested specifically for Ubuntu Bionic 18.04"
  echo "WARNING: The software lifecycle of the platform includes full support for all Ubuntu LTS versions starting from Ubuntu Xenial 16.04"

  prompt_for_continuation
fi

if [ ! -f /etc/timezone ]; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get install -y tzdata
  echo "Etc/UTC" > /etc/timezone
  dpkg-reconfigure -f noninteractive tzdata
  unset DEBIAN_FRONTEND
fi


# stops globaleaks if it is running
if ! ps aux | grep -q "[g]lobaleaks"; then
  DO "/etc/init.d/globaleaks stop"
fi

# align apt-get cache to up-to-date state on configured repositories
DO "apt-get -y update"

# fix curl requirement
if which curl >/dev/null; then
  echo " + curl requirement met"
else
  echo " - curl requirement not met. Installing curl"
  DO "apt-get -y install curl"
fi

# fix netstat requirement
if which netstat >/dev/null; then
  echo " + netstat requirement met"
else
  echo " - netstat requirement not met. Installing net-tools"
  DO "apt-get -y install net-tools"
fi

function is_tcp_sock_free_check {
  ! netstat -tlpn 2>/dev/null | grep -F $1 -q
}

# check the required sockets to see if they are already used
for SOCK in "0.0.0.0:80" "0.0.0.0:443" "127.0.0.1:8082" "127.0.0.1:8083"
do
  DO "is_tcp_sock_free_check $SOCK"
done

echo " + required TCP sockets open"


# The supported platforms are experimentally more than only Ubuntu as
# publicly communicated to users.
#
# Depending on the intention of the user to proceed anyhow installing on
# a not supported distro we using the experimental package if it exists
# or xenial as fallback.
if echo "$DISTRO_CODENAME" | grep -vqE "^(bionic|xenial|stretch)$"; then
  # In case of unsupported platforms we fallback on Bionic
  echo "No packages available for the current distribution; the install script will use the Bionic repository."
  echo "In case of a failure refer to the wiki for manual setup possibilities."
  echo "GlobaLeaks wiki: https://github.com/globaleaks/GlobaLeaks/wiki"
  DISTRO="Ubuntu"
  DISTRO_CODENAME="bionic"
fi

echo "Adding GlobaLeaks PGP key to trusted APT keys"
TMPFILE=$TMPDIR/globaleaks_key
echo "$GLOBALEAKS_PGP_KEY" > $TMPFILE
DO "apt-key add $TMPFILE"
DO "rm $TMPFILE"


if echo "$DISTRO_CODENAME" | grep -qE "^(wheezy)$"; then
  echo "Installing python-software-properties"
  DO "apt-get -y install python-software-properties"
else
  echo "Installing software-properties-common"
  DO "apt-get -y install software-properties-common"
fi

# try adding universe repo only on Ubuntu
if echo "$DISTRO" | grep -qE "^(Ubuntu)$"; then

  if ! grep -q "^deb .*universe" /etc/apt/sources.list /etc/apt/sources.list.d/*; then
    echo "Adding Ubuntu Universe repository"
    DO "add-apt-repository -y 'deb http://archive.ubuntu.com/ubuntu $DISTRO_CODENAME universe'"
  fi
fi

if [ -d /globaleaks/deb ]; then
  DO "apt-get -y update"
  DO "apt-get -y install dpkg-dev"
  echo "Installing from locally provided debian package"
  cd /globaleaks/deb/ && dpkg-scanpackages . /dev/null | gzip -c -9 > /globaleaks/deb/Packages.gz
  if [ ! -f /etc/apt/sources.list.d/globaleaks.local.list ]; then
    echo "deb file:///globaleaks/deb/ /" >> /etc/apt/sources.list.d/globaleaks.local.list
  fi
  DO "sudo apt -o Acquire::AllowInsecureRepositories=true -o Acquire::AllowDowngradeToInsecureRepositories=true update"
  DO "apt-get -y --allow-unauthenticated install globaleaks"
  DO "/etc/init.d/globaleaks restart"
else
  echo "Updating GlobaLeaks apt source.list in /etc/apt/sources.list.d/globaleaks.list ..."
  echo "deb http://deb.globaleaks.org $DISTRO_CODENAME/" > /etc/apt/sources.list.d/globaleaks.list
  DO "apt-get update -y"
  DO "apt-get install globaleaks -y"
fi

# Set the script to its success condition
last_command "startup"
last_status "0"

i=0
while [ $i -lt 30 ]
do
  X=$(netstat -tln | grep "127.0.0.1:8082")
  if [ $? -eq 0 ]; then
    #SUCCESS
    echo "Install script completed."
    IPS=$(/sbin/ip -4 -o addr show | awk '{split($4,a,"/");print a[1]}')
    echo "GlobaLeaks should be reachable at:"
    for IP in $IPS;
    do
      echo "+ http://$IP"
    done
    exit 0
  fi
  i=$[$i+1]
  sleep 1
done

#ERROR
echo "Ouch! The installation is complete but GlobaLeaks failed to start."
last_status "1"
exit 1
