#!/bin/bash

set -e

if [ -z "$GLREQUIREMENTS" ]; then
  GLREQUIREMENTS="trusty"
fi

TRAVIS_USR="travis-`git rev-parse --short HEAD`"

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
  pip install coverage coveralls
}

setupDependencies() {
  setupClientDependencies $1
  setupBackendDependencies
}

npm install -g grunt grunt-cli

if [ "$GLTEST" = "test" ]; then

  echo "Running backend unit tests"
  setupDependencies
  cd $TRAVIS_BUILD_DIR/backend
  coverage run setup.py test

  echo "Running API tests"
  $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z $TRAVIS_USR --disable-mail-notification
  sleep 3
  cd $TRAVIS_BUILD_DIR/client
  grunt mochaTest

  if [ "$GLREQUIREMENTS" = "trusty" ]; then
    echo "Extracting firefox and setting PATH variable..."
    tar -xjf /tmp/firefox-46.0.tar.bz2 --directory /tmp
    export PATH="/tmp/firefox:$PATH"
    echo "Using firefox version `firefox --version`"

    npm install -g istanbul

    echo "Running BrowserTesting locally collecting code coverage"
    cd $TRAVIS_BUILD_DIR/client

    grunt end2end-coverage-instrument

    $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z $TRAVIS_USR -c -k9 --disable-mail-notification
    sleep 3

    cd $TRAVIS_BUILD_DIR/client
    node_modules/protractor/bin/webdriver-manager update
    node_modules/protractor/bin/protractor tests/end2end/protractor-coverage.config.js
    grunt end2end-coverage-report

    cd $TRAVIS_BUILD_DIR/backend

    coveralls --merge=../client/coverage/coveralls.json
  fi

elif [ "$GLTEST" = "lint" ]; then

  setupDependencies

  pip install pylint
  echo "Running pylint checks"
  cd $TRAVIS_BUILD_DIR/backend
  pylint globaleaks -E --disable=no-value-for-parameter

  echo "Running eslint checks"
  cd $TRAVIS_BUILD_DIR/client
  grunt eslint

elif [ "$GLTEST" = "build_and_install" ]; then

  echo "Running Build & Install and BrowserTesting tests"
  # we build all packages to test build for each distributions and then we test against trusty
  sudo apt-get update -y
  sudo apt-get install -y debhelper devscripts dh-apparmor dh-python python python-pip python-setuptools python-sphinx
  curl -sL https://deb.nodesource.com/setup | sudo bash -
  sudo apt-get install -y nodejs
  cd $TRAVIS_BUILD_DIR
  ./scripts/build.sh -d trusty -t $TRAVIS_COMMIT -n
  sudo mkdir -p /data/globaleaks/deb/
  sudo cp GLRelease-trusty/globaleaks*deb /data/globaleaks/deb/
  set +e # avoid to fail in case of errors cause apparmor will always cause the failure
  sudo ./scripts/install.sh
  set -e # re-enable to fail in case of errors
  sudo sh -c 'echo "NETWORK_SANDBOXING=0" >> /etc/default/globaleaks'
  sudo sh -c 'echo "APPARMOR_SANDBOXING=0" >> /etc/default/globaleaks'
  # Inject content into the db while its hot. #TODO move hardcoded paths
  sleep 5
  sudo sh -c 'sqlite3 /var/globaleaks/db/glbackend-36.db < $TRAVIS_BUILD_DIR/backend/globaleaks/tests/data/post_init.sql'
  sudo /etc/init.d/globaleaks restart
  sleep 5
  setupClientDependencies
  cd $TRAVIS_BUILD_DIR/client
  node_modules/protractor/bin/webdriver-manager update
  node_modules/protractor/bin/protractor tests/end2end/protractor.config.js

elif [[ $GLTEST =~ ^end2end-.* ]]; then

  echo "Running Browsertesting on Saucelabs"

  declare -a capabilities=(
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"MicrosoftEdge\", \"version\":\"14.14393\", \"platform\":\"Windows 10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Internet Explorer\", \"version\":\"11\", \"platform\":\"Windows 10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Firefox\", \"version\":\"34\", \"platform\":\"Linux\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Firefox\", \"version\":\"46\", \"platform\":\"Windows 10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Chrome\", \"version\":\"37\", \"platform\":\"Linux\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Chrome\", \"version\":\"55\", \"platform\":\"Windows 10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Safari\", \"version\":\"8\", \"platform\":\"OS X 10.10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Safari\", \"version\":\"9\", \"platform\":\"OS X 10.11\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Android\", \"version\": \"4.4\", \"deviceName\": \"Android Emulator\", \"deviceOrientation\": \"portrait\", \"deviceType\": \"tablet\", \"platform\": \"Linux\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"Android\", \"version\": \"5.1\", \"deviceName\": \"Android Emulator\", \"deviceOrientation\": \"portrait\", \"deviceType\": \"tablet\", \"platform\": \"Linux\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\": \"Safari\", \"platformName\":\"iOS\", \"platformVersion\": \"8.1\", \"deviceName\": \"iPad Simulator\", \"deviceOrientation\": \"portrait\", \"appium-version\":\"1.5.3\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\": \"Safari\", \"platformName\":\"iOS\", \"platformVersion\": \"9.3\", \"deviceName\": \"iPad Simulator\", \"deviceOrientation\": \"portrait\", \"appium-version\":\"1.5.3\"}'"
  )

  testkey=$(echo $GLTEST | cut -f2 -d-)

  ## now loop through the above array
  capability=${capabilities[${testkey}]}

  echo "Testing Configuration: ${testkey}"
  setupDependencies 1
  eval $capability
  $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z $TRAVIS_USR --port 3000 --disable-mail-torification
  sleep 5
  sudo sh -c 'sqlite3 $TRAVIS_BUILD_DIR/backend/workingdir/db/glbackend-36.db < $TRAVIS_BUILD_DIR/backend/globaleaks/tests/data/post_init.sql'
  cd $TRAVIS_BUILD_DIR/client
  node_modules/protractor/bin/protractor tests/end2end/protractor-sauce.config.js

fi
