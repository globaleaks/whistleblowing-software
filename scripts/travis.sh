#!/bin/bash

set -e

if [ -z "$GLREQUIREMENTS" ]; then
  GLREQUIREMENTS="trusty"
fi

TRAVIS_USR="travis-$(git rev-parse --short HEAD)"

setupClientDependencies() {
  cd $TRAVIS_BUILD_DIR/client  # to install frontend dependencies
  npm install -d
  grunt copy:sources
  if [ "$1" = 1 ]; then
    grunt build
  fi
}

setupBackendDependencies() {
  cd $TRAVIS_BUILD_DIR/backend  # to install backend dependencies
  rm -rf requirements.txt
  ln -s requirements/requirements-${GLREQUIREMENTS}.txt requirements.txt
  pip install -r requirements.txt
}

setupDependencies() {
  setupClientDependencies $1
  setupBackendDependencies
}

sudo iptables -t nat -A OUTPUT -o lo -p tcp --dport 9000 -j REDIRECT --to-port 8082

npm install -g grunt grunt-cli

if [ "$GLTEST" = "test" ]; then
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

  node_modules/protractor/bin/webdriver-manager update

  grunt protractor_coverage
  grunt end2end-coverage-report

  cd $TRAVIS_BUILD_DIR/backend

  coveralls --merge=../client/coverage/coveralls.json

elif [ "$GLTEST" = "lint" ]; then
  pip install pylint==1.6.5

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

  echo "Running Build & Install and BrowserTesting tests"
  # we build all packages to test build for each distributions and then we test against trusty
  sudo apt-get update -y
  sudo apt-get install -y debhelper devscripts dh-apparmor dh-python python python-pip python-setuptools python-sphinx
  curl -sL https://deb.nodesource.com/setup | sudo bash -
  sudo apt-get install -y nodejs
  cd $TRAVIS_BUILD_DIR
  sed -ie 's/key_bits = 2048/key_bits = 512/g' backend/globaleaks/settings.py
  sed -ie 's/csr_sign_bits = 512/csr_sign_bits = 256/g' backend/globaleaks/settings.py
  rm debian/control backend/requirements.txt
  cp debian/controlX/control.trusty debian/control
  cp backend/requirements/requirements-trusty.txt backend/requirements.txt
  cd client
  npm install grunt-cli
  npm install
  grunt build
  cd ..
  debuild -i -us -uc -b
  sudo mkdir -p /globaleaks/deb/
  sudo cp ../globaleaks*deb /globaleaks/deb/
  sudo ./scripts/install.sh --assume-yes --test
  setupClientDependencies
  cd $TRAVIS_BUILD_DIR/client
  node_modules/protractor/bin/webdriver-manager update
  node_modules/protractor/bin/protractor tests/end2end/protractor.config.js

elif [[ $GLTEST =~ ^end2end-.* ]]; then

  echo "Running Browsertesting on Saucelabs"

  declare -a capabilities=(
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"MicrosoftEdge\", \"version\":\"15.15063\", \"platform\":\"Windows 10\", \"seleniumVersion\":\"3.5.3\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Internet Explorer\", \"version\":\"11.103\", \"platform\":\"Windows 10\", \"seleniumVersion\":\"3.5.3\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Firefox\", \"version\":\"34\", \"platform\":\"OS X 10.12\", \"seleniumVersion\":\"3.5.3\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Firefox\", \"version\":\"54\", \"platform\":\"OS X 10.12\", \"seleniumVersion\":\"3.5.3\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Chrome\", \"version\":\"37\",  \"platform\":\"OS X 10.12\", \"seleniumVersion\":\"3.5.3\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Chrome\", \"version\":\"59\", \"platform\":\"OS X 10.12\", \"seleniumVersion\":\"3.5.3\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Safari\", \"version\":\"8\", \"platform\":\"OS X 10.10\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Safari\", \"version\":\"10\", \"platform\":\"macOS 10.12\", \"seleniumVersion\":\"3.5.3\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Browser\", \"platformName\":\"Android\", \"platformVersion\": \"4.4\", \"deviceName\": \"Android Emulator\", \"deviceOrientation\": \"portrait\", \"appiumVersion\":\"1.7.1\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Chrome\", \"platformName\":\"Android\", \"platformVersion\": \"6.0\", \"deviceName\": \"Android Emulator\", \"deviceOrientation\": \"portrait\", \"appiumVersion\":\"1.7.1\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\": \"Safari\", \"platformName\":\"iOS\", \"platformVersion\": \"8.1\", \"deviceName\": \"iPad Simulator\", \"deviceOrientation\": \"portrait\", \"appium-version\":\"1.7.1\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\": \"Safari\", \"platformName\":\"iOS\", \"platformVersion\": \"11.0\", \"deviceName\": \"iPad Air 2 Simulator\", \"deviceOrientation\": \"portrait\", \"appium-version\":\"1.7.1\", \"maxDuration\":\"7200\", \"commandTimeout\":\"600\", \"idleTimeout\":\"270\"}'"
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
