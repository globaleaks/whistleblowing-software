#!/bin/bash

set -e

TRAVIS_USR="travis-$(git rev-parse --short HEAD)"

LOGFILE="$TRAVIS_BUILD_DIR/backend/workingdir/log/globaleaks.log"
ACCESSLOG="$TRAVIS_BUILD_DIR/backend/workingdir/log/access.log"

function atexit {
  if [[ -f $LOGFILE ]]; then
    cat $LOGFILE
  fi

  if [[ -f $ACCESSLOG ]]; then
    cat $ACCESSLOG
  fi
}

trap atexit EXIT

setupClientDependencies() {
  cd $TRAVIS_BUILD_DIR/client  # to install frontend dependencies
  npm install
  grunt instrument-client
}

setupBackendDependencies() {
  cd $TRAVIS_BUILD_DIR/backend  # to install backend dependencies
  pip3 install -r requirements/requirements-$(lsb_release -cs).txt
}

setupDependencies() {
  setupClientDependencies
  setupBackendDependencies
}

sudo apt-get update
sudo apt-get install -y tor
npm install -g grunt grunt-cli

if [ "$GLTEST" = "test" ]; then
  pip install coverage

  echo "Running backend unit tests"
  setupDependencies
  cd $TRAVIS_BUILD_DIR/backend && coverage run setup.py test

  $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z -d
  sleep 5

  echo "Running BrowserTesting locally collecting code coverage"
  cd $TRAVIS_BUILD_DIR/client && npm test


  if [ -n "CODACY" ]; then
    cd $TRAVIS_BUILD_DIR/backend && coverage xml
    bash <(curl -Ls https://coverage.codacy.com/get.sh) report -l Python -r $TRAVIS_BUILD_DIR/backend/coverage.xml
    bash <(curl -Ls https://coverage.codacy.com/get.sh) report -l Javascript -r $TRAVIS_BUILD_DIR/client/cypress/coverage/lcov.info
    bash <(curl -Ls https://coverage.codacy.com/get.sh) final
  fi
elif [ "$GLTEST" = "build_and_install" ]; then
  LOGFILE="/var/globaleaks/log/globaleaks.log"
  ACCESSLOG="/var/globaleaks/log/accesslog.log"

  sudo apt-get install -y debootstrap

  export chroot="/tmp/globaleaks_chroot/"
  sudo mkdir -p "$chroot/build"
  sudo cp -R $TRAVIS_BUILD_DIR/ "$chroot/build"
  export LC_ALL=en_US.utf8
  export DEBIAN_FRONTEND=noninteractive

  if [ $DISTRIBUTION = "bookworm" ]; then
    sudo -E debootstrap --arch=amd64 bookworm "$chroot" http://deb.debian.org/debian/
    sudo -E su -c 'echo "deb http://deb.debian.org/debian bookworm main contrib" > /tmp/globaleaks_chroot/etc/apt/sources.list'
    sudo -E su -c 'echo "deb http://deb.debian.org/debian bookworm main contrib" >> /tmp/globaleaks_chroot/etc/apt/sources.list'
  elif [ $DISTRIBUTION = "jammy" ]; then
    sudo -E debootstrap --arch=amd64 jammy "$chroot" http://archive.ubuntu.com/ubuntu/
    sudo -E su -c 'echo "deb http://archive.ubuntu.com/ubuntu jammy main universe" > /tmp/globaleaks_chroot/etc/apt/sources.list'
    sudo -E su -c 'echo "deb http://archive.ubuntu.com/ubuntu jammy-updates main universe" >> /tmp/globaleaks_chroot/etc/apt/sources.list'
  fi

  sudo -E mount --rbind /proc "$chroot/proc"
  sudo -E mount --rbind /sys "$chroot/sys"

  sudo -E chroot "$chroot" apt-get update -y
  sudo -E chroot "$chroot" apt-get upgrade -y

  sudo -E chroot "$chroot" apt-get install -y lsb-release locales sudo

  sudo -E su -c 'echo "en_US.UTF-8 UTF-8" >> /tmp/globaleaks_chroot/etc/locale.gen'
  sudo -E chroot "$chroot" locale-gen

  sudo -E chroot "$chroot" useradd -m builduser
  sudo -E su -c 'echo "builduser ALL=NOPASSWD: ALL" >> "$chroot"/etc/sudoers'
  sudo -E chroot "$chroot" chown builduser -R /build
  sudo -E chroot "$chroot" su - builduser /bin/bash -c '/build/GlobaLeaks/travis/build_and_install.sh'
fi
