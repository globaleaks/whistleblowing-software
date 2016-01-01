#!/bin/bash

set -e

if ! [ -z "$GLREQUIREMENTS" ]; then
  GLREQUIREMENTS="trusty"
fi

setupClientDependencies()
{
  cd $TRAVIS_BUILD_DIR/client  # to install frontend dependencies
  npm install -g grunt grunt-cli bower
  npm install -d
  grunt setupDependencies
  ./node_modules/protractor/bin/webdriver-manager update
  grunt build
}

setupBackendDependencies()
{
  cd $TRAVIS_BUILD_DIR/backend  # to install backend dependencies
  rm -rf requirements.txt
  ln -s requirements/requirements-${GLREQUIREMENTS}.txt requirements.txt
  pip install -r requirements.txt
  pip install coverage coveralls
}

setupDependencies()
{
  setupClientDependencies
  setupBackendDependencies
}

if [ "$GLTEST" = "unit" ]; then

  echo "Running API tests"
  setupDependencies
  cd $TRAVIS_BUILD_DIR/backend
  coverage run setup.py test

  $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z travis --disable-mail-notification
  sleep 5
  $TRAVIS_BUILD_DIR/client/node_modules/mocha/bin/mocha -R list $TRAVIS_BUILD_DIR/client/tests/api/test_00* --timeout 30000

  echo "Running BrowserTesting locally collecting code coverage"
  cd $TRAVIS_BUILD_DIR/client
  rm -fr $TRAVIS_BUILD_DIR/client/coverage

  $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z travis -c -k9 --disable-mail-notification
  sleep 5

  cd $TRAVIS_BUILD_DIR/client
  grunt end2end-coverage

  cd $TRAVIS_BUILD_DIR/backend
  coveralls --merge=../client/coverage/coveralls.json || true

elif [ "$GLTEST" = "build_and_install" ]; then

  echo "Running Build & Install and BrowserTesting tests"
  # we build all packages to test build for each distributions and then we test against trusty
  sudo apt-get update -y
  sudo apt-get install -y debhelper devscripts dh-apparmor dh-python python python-pip python-setuptools python-sphinx
  curl -sL https://deb.nodesource.com/setup | sudo bash -
  sudo apt-get install -y nodejs
  cd $TRAVIS_BUILD_DIR
  ./scripts/build.sh -d all -t $TRAVIS_COMMIT -n
  sudo mkdir -p /data/globaleaks/deb/
  sudo cp GLRelease-trusty/globaleaks*deb /data/globaleaks/deb/
  set +e # avoid to fail in case of errors cause apparmor will always cause the failure
  sudo ./scripts/install.sh
  set -e # re-enable to fail in case of errors
  sudo sh -c 'echo "NETWORK_SANDBOXING=0" >> /etc/default/globaleaks'
  sudo sh -c 'echo "APPARMOR_SANDBOXING=0" >> /etc/default/globaleaks'
  sudo /etc/init.d/globaleaks restart
  sleep 5
  setupClientDependencies
  cd $TRAVIS_BUILD_DIR/client
  grunt protractor:test

elif [[ $GLTEST =~ ^end2end-.* ]]; then

  echo "Running Browsertesting on Saucelabs"

  declare -a capabilities=(
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"internet explorer\", \"version\":\"9\", \"platform\":\"Windows 7\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"internet explorer\", \"version\":\"10\", \"platform\":\"Windows 8\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"internet explorer\", \"version\":\"11\", \"platform\":\"Windows 10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"microsoftEdge\", \"version\":\"20.10240\", \"platform\":\"Windows 10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"firefox\", \"version\":\"34\", \"platform\":\"Linux\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"firefox\", \"version\":\"42\", \"platform\":\"Linux\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"chrome\", \"version\":\"37\", \"platform\":\"Linux\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"chrome\", \"version\":\"46\", \"platform\":\"Linux\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"safari\", \"version\":\"8\", \"platform\":\"OS X 10.10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"safari\", \"version\":\"9\", \"platform\":\"OS X 10.11\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"android\", \"version\": \"4.4\", \"deviceName\": \"Android Emulator\", \"platform\": \"Linux\"}'."
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"android\", \"version\": \"5.1\", \"deviceName\": \"Android Emulator\", \"platform\": \"Linux\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\": \"iPhone\", \"version\": \"7.1\", \"deviceName\": \"iPad Simulator\", \"device-orientation\": \"portrait\", \"platform\":\"OS X 10.10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\": \"iPhone\", \"version\": \"9.1\", \"deviceName\": \"iPad Simulator\", \"device-orientation\": \"portrait\", \"platform\":\"OS X 10.10\"}'"
  )

  testkey=$(echo $GLTEST | cut -f2 -d-)

  ## now loop through the above array
  capability=${capabilities[${testkey}]}

  echo "Testing Configuration: ${testkey}"
  setupDependencies
  eval $capability
  $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z travis --port 9000 --disable-mail-torification
  sleep 5
  cd $TRAVIS_BUILD_DIR/client
  grunt protractor:saucelabs

fi
