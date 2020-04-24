#!/bin/bash

set -e

if [ -z "$DISTRIBUTION" ]; then
  DISTRIBUTION=$(lsb_release -cs)
fi

TRAVIS_USR="travis-$(git rev-parse --short HEAD)"

setupChrome() {
  export CHROME_BIN=/usr/bin/google-chrome
  export DISPLAY=:99.0
  wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
  sudo dpkg -i google-chrome*.deb
  /sbin/start-stop-daemon --start --quiet --pidfile /tmp/custom_xvfb_99.pid --make-pidfile --background --exec /usr/bin/Xvfb -- :99 -ac -screen 0 1280x1024x16
}

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
  pip3 install -r requirements/requirements-$DISTRIBUTION.txt
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
  setupChrome

  pip install coverage codacy-coverage
  npm install -g istanbul codacy-coverage

  echo "Running backend unit tests"
  setupDependencies
  cd $TRAVIS_BUILD_DIR/backend
  coverage run setup.py test

  echo "Running BrowserTesting locally collecting code coverage"
  cd $TRAVIS_BUILD_DIR/client
  ./node_modules/nyc/bin/nyc.js  instrument --complete-copy app build --source-map=false

  $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z $TRAVIS_USR -k9 -D
  sleep 3

  ./node_modules/protractor/bin/webdriver-manager update --versions.chrome 80.0.3987.106

  ./node_modules/protractor/bin/protractor tests/protractor-coverage.config.js

  if [ -n "CODACY" ]; then
    cd $TRAVIS_BUILD_DIR/backend
    coverage xml
    python-codacy-coverage -r coverage.xml -c $TRAVIS_COMMIT # Python

    cd $TRAVIS_BUILD_DIR/client
    ./node_modules/nyc/bin/nyc.js report --reporter=lcov
    cat coverage/lcov.info | codacy-coverage -c $TRAVIS_COMMIT # Javascript
  fi
elif [ "$GLTEST" = "docker" ]; then
  cd $TRAVIS_BUILD_DIR/docker && ./build.sh
elif [ "$GLTEST" = "build_and_install" ]; then
  function atexit {
    if [[ ! $? -eq 0 && -f /var/globaleaks/log/globaleaks.log ]]; then
      cat /var/globaleaks/log/globaleaks.log
    fi
  }

  trap atexit EXIT

  sudo apt-get install -y debootstrap

  export chroot="/tmp/globaleaks_chroot/"
  mkdir -p "$chroot/build"
  sudo cp -R $TRAVIS_BUILD_DIR/ "$chroot/build"
  export LC_ALL=en_US.utf8

  if [ $DISTRIBUTION = "bionic" ]; then
    sudo debootstrap --arch=amd64 bionic "$chroot" http://archive.ubuntu.com/ubuntu/
    sudo su -c 'echo "deb http://archive.ubuntu.com/ubuntu bionic main universe" > /tmp/globaleaks_chroot/etc/apt/sources.list'
    sudo su -c 'echo "deb http://archive.ubuntu.com/ubuntu bionic-updates main universe" >> /tmp/globaleaks_chroot/etc/apt/sources.list'
  elif [ $DISTRIBUTION = "focal" ]; then
    sudo debootstrap --arch=amd64 focal "$chroot" http://archive.ubuntu.com/ubuntu/
    sudo su -c 'echo "deb http://archive.ubuntu.com/ubuntu focal main universe" > /tmp/globaleaks_chroot/etc/apt/sources.list'
    sudo su -c 'echo "deb http://archive.ubuntu.com/ubuntu focal-updates main universe" >> /tmp/globaleaks_chroot/etc/apt/sources.list'
  elif [ $DISTRIBUTION = "buster" ]; then
    sudo debootstrap --arch=amd64 buster "$chroot" http://deb.debian.org/debian/
    sudo su -c 'echo "deb http://deb.debian.org/debian buster main contrib" > /tmp/globaleaks_chroot/etc/apt/sources.list'
    sudo su -c 'echo "deb http://deb.debian.org/debian buster main contrib" >> /tmp/globaleaks_chroot/etc/apt/sources.list'
  fi

  if [ $DISTRIBUTION = "bionic" ]; then
    sudo mount --rbind /dev/pts "$chroot/dev/pts"
  fi

  sudo mount --rbind /proc "$chroot/proc"
  sudo mount --rbind /sys "$chroot/sys"

  sudo chroot "$chroot" apt-get update -y
  sudo chroot "$chroot" apt-get upgrade -y

  sudo chroot "$chroot" apt-get install -y lsb-release locales sudo

  sudo su -c 'echo "en_US.UTF-8 UTF-8" >> /tmp/globaleaks_chroot/etc/locale.gen'
  sudo chroot "$chroot" locale-gen

  sudo chroot "$chroot" useradd -m builduser
  sudo su -c 'echo "builduser ALL=NOPASSWD: ALL" >> "$chroot"/etc/sudoers'
  sudo chroot "$chroot" chown builduser -R /build
  sudo chroot "$chroot" su - builduser /bin/bash -c '/build/GlobaLeaks/travis/build_and_install.sh'
elif [[ $GLTEST =~ ^end2end-.* ]]; then
  echo "Running Browsertesting on Saucelabs"

  declare -a capabilities=(
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Chrome\", \"version\":\"80\", \"platform\":\"macOS 10.15\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Firefox\", \"version\":\"74.0\", \"platform\":\"macOS 10.15\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Safari\", \"version\":\"13.0\", \"platform\":\"macOS 10.15\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"MicrosoftEdge\", \"version\":\"80.0\", \"platform\":\"Windows 10\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Internet Explorer\", \"version\":\"11.285\", \"platform\":\"Windows 10\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Chrome\", \"platformName\":\"Android\", \"platformVersion\": \"10.0\", \"deviceName\": \"Android GoogleAPI Emulator\", \"deviceOrientation\": \"portrait\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\": \"Safari\", \"platformName\":\"iOS\", \"platformVersion\": \"13.2\", \"deviceName\": \"iPhone XS Simulator\", \"deviceOrientation\": \"portrait\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
  )

  testkey=$(echo $GLTEST | cut -f2 -d-)

  ## now loop through the above array
  capability=${capabilities[${testkey}]}

  echo "Testing Configuration: ${testkey}"
  setupDependencies 1
  eval $capability
  $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z $TRAVIS_USR
  sleep 3
  cd $TRAVIS_BUILD_DIR/client
  node_modules/protractor/bin/protractor tests/protractor-sauce.config.js
fi
