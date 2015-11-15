#!/bin/bash

set -e

setupDependencies ()
{
  cd $TRAVIS_BUILD_DIR/backend  # to install backend dependencies
  pip install -r requirements.txt
  pip install coverage coveralls
  cd $TRAVIS_BUILD_DIR/client  # to install frontend dependencies
  npm install -g grunt grunt-cli bower
  npm install
  grunt setupDependencies
  grunt build
}

if [ "$GLTEST" = "unit" ]; then

  echo "Running Mocha testes for API"
  setupDependencies
  cd $TRAVIS_BUILD_DIR/backend
  coverage run setup.py test

  $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z travis --disable-mail-notification
  sleep 5
  $TRAVIS_BUILD_DIR/client/node_modules/mocha/bin/mocha -R list $TRAVIS_BUILD_DIR/client/tests/api/test_00* --timeout 30000

  echo "Running Protractor End2End locally for coverage"
  cd $TRAVIS_BUILD_DIR/client
  rm -fr $TRAVIS_BUILD_DIR/client/coverage
  ./node_modules/protractor/bin/webdriver-manager update

  $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z travis -c -k9 --disable-mail-notification
  sleep 5
  grunt end2end-coverage

  cd $TRAVIS_BUILD_DIR/backend
  coveralls --merge=../client/coverage/coveralls.json || true

elif [ "$GLTEST" = "build_and_install" ]; then

  echo "Running Build & Install test"
  sudo apt-get update -y
  sudo apt-get install -y debhelper devscripts dh-apparmor dh-python python python-pip python-setuptools python-sphinx
  curl -sL https://deb.nodesource.com/setup | sudo bash -
  sudo apt-get install -y nodejs
  cd $TRAVIS_BUILD_DIR
  ./scripts/build.sh -d trusty -t $TRAVIS_COMMIT -n
  sudo mkdir -p /data/globaleaks/deb/
  sudo cp GLRelease/globaleaks*deb /data/globaleaks/deb/
  set +e # avoid to fail in case of errors cause apparmor will always cause the failure
  sudo ./scripts/install.sh
  set -e # re-enable to fail in case of errors
  sudo sed -i 's/NETWORK_SANDBOXING=1/NETWORK_SANDBOXING=0/g' /etc/default/globaleaks
  sudo sed -i 's/APPARMOR_SANDBOXING=1/APPARMOR_SANDBOXING=0/g' /etc/default/globaleaks
  sudo /etc/init.d/globaleaks restart
  sleep 5
  curl 127.0.0.1:8082 | grep "GlobaLeaks"

elif [ "$GLTEST" = "browserchecks" ]; then

  echo "Running Mocha tests for browser compatibility"
  setupDependencies
  grunt test-browserchecks-saucelabs

elif [[ $GLTEST =~ ^end2end-.* ]]; then

  echo "Running Protractor End2End tests"

  setupDependencies

  declare -a capabilities=(
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"firefox\", \"version\":\"34\", \"platform\":\"Windows 10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"firefox\", \"version\":\"42\", \"platform\":\"Windows 10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"chrome\", \"version\":\"37\", \"platform\":\"Windows 10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"chrome\", \"version\":\"46\", \"platform\":\"Windows 10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"safari\", \"version\":\"8\", \"platform\":\"OS X 10.10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"safari\", \"version\":\"9\", \"platform\":\"OS X 10.11\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"internet explorer\", \"version\":\"9\", \"platform\":\"Windows 7\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"internet explorer\", \"version\":\"10\", \"platform\":\"Windows 7\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"internet explorer\", \"version\":\"11\", \"platform\":\"Windows 10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"microsoftedge\", \"version\":\"20.10240\", \"platform\":\"Windows 10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"android\", \"version\": \"4.4\", \"deviceName\": \"Android Emulator\", \"platform\": \"Linux\""
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"android\", \"version\": \"5.1\", \"deviceName\": \"Android Emulator\", \"platform\": \"Linux\""
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\": \"iPhone\", \"deviceName\": \"iPhone Retina (4-inch 64-bit)\", \"device-orientation\": \"portrait\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\": \"iPhone\", \"version\": \"9.1\", \"deviceName\": \"iPhone 6 Plus\", \"device-orientation\": \"portrait\", \"platform\":\"OS X 10.10\"}'"
  )

  index=$(echo $GLTEST | cut -f2 -d-)

  ## now loop through the above array
  capability=${capabilities[$index]}

  echo "Testing Configuration: $capability"
  setupDependencies
  eval $capability
  $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z travis --port 9000 --disable-mail-torification
  sleep 3
  grunt protractor:saucelabs

fi
