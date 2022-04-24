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
  grunt copy:sources
  if [ "$1" = 1 ]; then
    grunt build
  fi
}

setupBackendDependencies() {
  cd $TRAVIS_BUILD_DIR/backend  # to install backend dependencies
  pip3 install -r requirements/requirements-$(lsb_release -cs).txt
}

setupDependencies() {
  setupClientDependencies $1
  setupBackendDependencies
}

sudo apt-get update
sudo apt-get install -y tor
sudo usermod -aG debian-tor $USER
sudo iptables -t nat -A OUTPUT -o lo -p tcp --dport 9000 -j REDIRECT --to-port 8082
npm install -g grunt grunt-cli

if [ "$GLTEST" = "test" ]; then
  pip install coverage
  npm install -g istanbul

  echo "Running backend unit tests"
  setupDependencies
  cd $TRAVIS_BUILD_DIR/backend && coverage run setup.py test

  echo "Running BrowserTesting locally collecting code coverage"
  cd $TRAVIS_BUILD_DIR/client && ./node_modules/nyc/bin/nyc.js  instrument --complete-copy app build --source-map=false

  $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z -d
  sleep 3

  ./node_modules/protractor/bin/webdriver-manager update

  ./node_modules/protractor/bin/protractor tests/protractor-coverage.config.js

  if [ -n "CODACY" ]; then
    cd $TRAVIS_BUILD_DIR/backend && coverage xml
    cd $TRAVIS_BUILD_DIR/client && ./node_modules/nyc/bin/nyc.js report --reporter=lcov
    bash <(curl -Ls https://coverage.codacy.com/get.sh) report -r $TRAVIS_BUILD_DIR/backend/coverage.xml -r $TRAVIS_BUILD_DIR/client/coverage/lcov.info
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

  if [ $DISTRIBUTION = "bullseye" ]; then
    sudo -E debootstrap --arch=amd64 bullseye "$chroot" http://deb.debian.org/debian/
    sudo -E su -c 'echo "deb http://deb.debian.org/debian bullseye main contrib" > /tmp/globaleaks_chroot/etc/apt/sources.list'
    sudo -E su -c 'echo "deb http://deb.debian.org/debian bullseye main contrib" >> /tmp/globaleaks_chroot/etc/apt/sources.list'
  elif [ $DISTRIBUTION = "focal" ]; then
    sudo -E debootstrap --arch=amd64 focal "$chroot" http://archive.ubuntu.com/ubuntu/
    sudo -E su -c 'echo "deb http://archive.ubuntu.com/ubuntu focal main universe" > /tmp/globaleaks_chroot/etc/apt/sources.list'
    sudo -E su -c 'echo "deb http://archive.ubuntu.com/ubuntu focal-updates main universe" >> /tmp/globaleaks_chroot/etc/apt/sources.list'
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
