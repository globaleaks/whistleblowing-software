#!/bin/bash

set -e

if [ -z "$TESTS_REQUIREMENTS" ]; then
  TESTS_REQUIREMENTS="bionic"
fi

if [ -z "$BUILD_DISTRO" ]; then
  BUILD_DISTRO="bionic"
fi

TRAVIS_USR="travis-$(git rev-parse --short HEAD)"

setupChrome() {
  export CHROME_BIN=/usr/bin/google-chrome
  export DISPLAY=:99.0
  sudo apt-get install -y libappindicator1 fonts-liberation
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
  rm -rf requirements.txt
  if [ "$GLTEST" = "py3_test" ]; then
    ln -s requirements/requirements-bionic.txt requirements.txt
  else
    ln -s requirements/requirements-xenial.txt requirements.txt
  fi
  pip install -r requirements.txt
}

setupDependencies() {
  setupClientDependencies $1
  setupBackendDependencies
}

sudo iptables -t nat -A OUTPUT -o lo -p tcp --dport 9000 -j REDIRECT --to-port 8082

wget  http://mirrors.kernel.org/ubuntu/pool/main/d/dpkg/dpkg_1.17.5ubuntu5.8_amd64.deb
sudo dpkg -i dpkg_1.17.5ubuntu5.8_amd64.deb

wget http://mirrors.kernel.org/ubuntu/pool/main/d/debootstrap/debootstrap_1.0.95_all.deb
sudo dpkg -i debootstrap_1.0.95_all.deb

npm install -g grunt grunt-cli

if [ "$GLTEST" = "py2_test" ] || [ "$GLTEST" = "py3_test" ]; then
  setupChrome

  pip install coveralls==1.0b1
  sudo apt-get install -y python-coverage tor

  sudo usermod -aG debian-tor $USER

  echo "Running backend unit tests"
  setupDependencies
  cd $TRAVIS_BUILD_DIR/backend
  coverage run setup.py test

  echo "Running API tests"
  $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z $TRAVIS_USR
  sleep 3
  cd $TRAVIS_BUILD_DIR/client
  grunt mochaTest

  npm install -g istanbul

  echo "Running BrowserTesting locally collecting code coverage"
  cd $TRAVIS_BUILD_DIR/client

  grunt end2end-coverage-instrument

  $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z $TRAVIS_USR -k9
  sleep 3

  node_modules/protractor/bin/webdriver-manager update --gecko=false

  grunt protractor_coverage
  grunt end2end-coverage-report

  cd $TRAVIS_BUILD_DIR/backend

  if [ -n "COVERALLS" ]; then
    coveralls --merge=../client/coverage/coveralls.json
  fi

elif [ "$GLTEST" = "lint" ]; then
  pip install pylint

  setupDependencies

  echo "Running pylint checks"
  cd $TRAVIS_BUILD_DIR/backend
  pylint -r n globaleaks

  echo "Running eslint checks"
  cd $TRAVIS_BUILD_DIR/client
  grunt eslint

elif [ "$GLTEST" = "build_and_install" ]; then
  function atexit {
    if [[ ! $? -eq 0 && -f /var/globaleaks/log/globaleaks.log ]]; then
      cat /var/globaleaks/log/globaleaks.log
    fi
  }

  trap atexit EXIT

  export chroot="/tmp/globaleaks_chroot/"
  mkdir -p "$chroot/build"
  sudo cp -R $TRAVIS_BUILD_DIR/ "$chroot/build"
  sudo apt-get update
  sudo apt-get install -y debootstrap
  export LC_ALL=en_US.utf8

  if [ $BUILD_DISTRO = "bionic" ]; then
    sudo debootstrap --arch=amd64 bionic "$chroot" http://archive.ubuntu.com/ubuntu/
    sudo su -c 'echo "deb http://archive.ubuntu.com/ubuntu bionic main universe" > /tmp/globaleaks_chroot/etc/apt/sources.list'
    sudo su -c 'echo "deb http://archive.ubuntu.com/ubuntu bionic-updates main universe" >> /tmp/globaleaks_chroot/etc/apt/sources.list'
  elif [ $BUILD_DISTRO = "xenial" ]; then
    sudo debootstrap --arch=amd64 xenial "$chroot" http://archive.ubuntu.com/ubuntu/
    sudo su -c 'echo "deb http://archive.ubuntu.com/ubuntu xenial main universe" > /tmp/globaleaks_chroot/etc/apt/sources.list'
    sudo su -c 'echo "deb http://archive.ubuntu.com/ubuntu xenial-updates main universe" >> /tmp/globaleaks_chroot/etc/apt/sources.list'
  elif [ $BUILD_DISTRO = "stretch" ]; then
    sudo debootstrap --arch=amd64 stretch "$chroot" http://deb.debian.org/debian/
    sudo su -c 'echo "deb http://deb.debian.org/debian stretch main contrib" > /tmp/globaleaks_chroot/etc/apt/sources.list'
    sudo su -c 'echo "deb http://deb.debian.org/debian stretch main contrib" >> /tmp/globaleaks_chroot/etc/apt/sources.list'
  fi

  if [ $BUILD_DISTRO = "bionic" ] || [ $BUILD_DISTRO = "xenial" ]; then
    sudo mount --rbind /dev/pts "$chroot/dev/pts"
  fi

  if [ $BUILD_DISTRO = "xenial" ]; then
    sudo mount --rbind /dev/shm "$chroot/dev/shm"
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

  setupChrome

  declare -a capabilities=(
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"MicrosoftEdge\", \"version\":\"17.17134\", \"platform\":\"Windows 10\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Internet Explorer\", \"version\":\"11.103\", \"platform\":\"Windows 10\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Firefox\", \"version\":\"34\", \"platform\":\"OS X 10.13\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Firefox\", \"version\":\"60\", \"platform\":\"OS X 10.13\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Chrome\", \"version\":\"37\",  \"platform\":\"OS X 10.13\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Chrome\", \"version\":\"67\", \"platform\":\"OS X 10.13\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Safari\", \"version\":\"8\", \"platform\":\"OS X 10.10\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Safari\", \"version\":\"11.1\", \"platform\":\"macOS 10.13\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Browser\", \"platformName\":\"Android\", \"platformVersion\": \"4.4\", \"deviceName\": \"Android Emulator\", \"deviceOrientation\": \"portrait\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Chrome\", \"platformName\":\"Android\", \"platformVersion\": \"6.0\", \"deviceName\": \"Android Emulator\", \"deviceOrientation\": \"portrait\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\": \"Safari\", \"platformName\":\"iOS\", \"platformVersion\": \"9.3\", \"deviceName\": \"iPad Simulator\", \"deviceOrientation\": \"portrait\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\": \"Safari\", \"platformName\":\"iOS\", \"platformVersion\": \"11.3\", \"deviceName\": \"iPad Simulator\", \"deviceOrientation\": \"portrait\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
  )

  testkey=$(echo $GLTEST | cut -f2 -d-)

  ## now loop through the above array
  capability=${capabilities[${testkey}]}

  echo "Testing Configuration: ${testkey}"
  setupDependencies 1
  eval $capability
  $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z $TRAVIS_USR
  sleep 5
  cd $TRAVIS_BUILD_DIR/client
  node_modules/protractor/bin/protractor tests/end2end/protractor-sauce.config.js
fi
