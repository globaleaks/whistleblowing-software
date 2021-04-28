#!/bin/bash

echo -e "Running the GlobaLeaks installation...\nIn case of failure please report encountered issues to the ticketing system at: https://github.com/globaleaks/GlobaLeaks/issues\n"

export DEBIAN_FRONTEND=noninteractive

# User Permission Check
if [ ! $(id -u) = 0 ]; then
  echo "Error: GlobaLeaks install script must be run by root"
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

DISTRO="unknown"
DISTRO_CODENAME="unknown"
if which lsb_release >/dev/null; then
  DISTRO="$(lsb_release -is)"
  DISTRO_CODENAME="$(lsb_release -cs)"
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

for arg in "$@"; do
  shift
  case "$arg" in
    --assume-yes ) ASSUMEYES=1; shift;;
    --install-experimental-version-and-accept-the-consequences ) EXPERIMENTAL=1; shift;;
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

if echo "$DISTRO_CODENAME" | grep -vqE "^buster$" ; then
  echo "WARNING: GlobaLeaks is actively developed and tested specifically for Debian 10 (Buster)"
  echo "WARNING: The software lifecycle of the platform includes full support for all Debian and Ubuntu LTS versions starting from Debian 10 and Ubuntu 20.04"

  prompt_for_continuation
fi

if [ -f /etc/init.d/globaleaks ]; then
  DO "/etc/init.d/globaleaks stop"
fi

# align apt-get cache to up-to-date state on configured repositories
DO "apt-get -y update"

if [ ! -f /etc/timezone ]; then
  echo "Etc/UTC" > /etc/timezone
fi

apt-get install -y tzdata
dpkg-reconfigure -f noninteractive tzdata

DO "apt-get -y install curl gnupg net-tools software-properties-common"

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
# or Buster as fallback.
if echo "$DISTRO_CODENAME" | grep -vqE "^(buster|focal|bionic)$"; then
  # In case of unsupported platforms we fallback on Bionic
  echo "No packages available for the current distribution; the install script will use the Bionic repository."
  echo "In case of a failure refer to the wiki for manual setup possibilities."
  echo "GlobaLeaks wiki: https://github.com/globaleaks/GlobaLeaks/wiki"
  DISTRO="Debian"
  DISTRO_CODENAME="buster"
fi

echo "Adding GlobaLeaks PGP key to trusted APT keys"
curl -L https://deb.globaleaks.org/globaleaks.asc | apt-key add

# try adding universe repo only on Ubuntu
if echo "$DISTRO" | grep -qE "^(Ubuntu)$"; then
  if ! grep -q "^deb .*universe" /etc/apt/sources.list /etc/apt/sources.list.d/*; then
    echo "Adding Ubuntu Universe repository"
    DO "add-apt-repository -y 'deb http://archive.ubuntu.com/ubuntu $DISTRO_CODENAME universe'"
  fi
fi

echo "Updating GlobaLeaks apt source.list in /etc/apt/sources.list.d/globaleaks.list ..."
echo "deb http://deb.globaleaks.org $DISTRO_CODENAME/" > /etc/apt/sources.list.d/globaleaks.list

if [ -d /globaleaks/deb ]; then
  DO "apt-get -y update"
  DO "apt-get -y install dpkg-dev"
  echo "Installing from locally provided debian package"
  cd /globaleaks/deb/ && dpkg-scanpackages . /dev/null | gzip -c -9 > /globaleaks/deb/Packages.gz
  if [ ! -f /etc/apt/sources.list.d/globaleaks.local.list ]; then
    echo "deb file:///globaleaks/deb/ /" >> /etc/apt/sources.list.d/globaleaks.local.list
  fi
  DO "apt -o Acquire::AllowInsecureRepositories=true -o Acquire::AllowDowngradeToInsecureRepositories=true update"
  DO "apt-get -y --allow-unauthenticated install globaleaks"
  DO "/etc/init.d/globaleaks restart"
else
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
    echo "GlobaLeaks setup completed."
    TOR=$(gl-admin getvar onionservice)
    echo "To proceed with the configuration you could now access the platvorm wizard at:"
    echo "+ http://$TOR (via the Tor Browser)"
    echo "+ http://127.0.0.1:8082"
    echo "+ http://0.0.0.0"
    echo "We recommend you to to perform the wizard by using Tor address or on localhost via a VPN."
    exit 0
  fi
  i=$[$i+1]
  sleep 1
done

#ERROR
echo "Ouch! The installation is complete but GlobaLeaks failed to start."
last_status "1"
exit 1
