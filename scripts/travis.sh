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
  coveralls || true
  $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z travis
  sleep 5
  $TRAVIS_BUILD_DIR/client/node_modules/mocha/bin/mocha -R list $TRAVIS_BUILD_DIR/client/tests/api/test_00* --timeout 30000

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
  find /etc/default/globaleaks -type f -print0 | xargs -0 sed -i 's/NETWORK_SANDBOXING=1/NETWORK_SANDBOXING=0/g'
  find /etc/default/globaleaks -type f -print0 | xargs -0 sed -i 's/APPARMOR_SANDBOXING=1/APPARMOR_SANDBOXING=0/g'
  sleep 5
  curl 127.0.0.1:8082 | grep "Hermes Center for Transparency and Digital Human Rights"

elif [ "$GLTEST" = "browserchecks" ]; then

  echo "Running Mocha tests for browser compatibility"
  setupDependencies
  grunt test-browserchecks-saucelabs

elif [ "$GLTEST" = "end2end" ]; then

  echo "Running Protractor End2End tests"

  setupDependencies

  declare -a capabilities=(
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"firefox\", \"version\":\"37.0\", \"platform\":\"Windows 10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"chrome\", \"version\":\"42.0\", \"platform\":\"Windows 10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"safari\", \"version\":\"8\", \"platform\":\"OS X 10.10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"internet explorer\", \"version\":\"11\", \"platform\":\"Windows 10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"microsoftedge\", \"version\":\"20.10240\", \"platform\":\"Windows 10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"android\", \"version\": \"5.1\", \"deviceName\": \"Android Emulator\", \"platform\": \"Linux\", \"platform\":\"OS X 10.10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\": \"iphone\", \"version\": \"8.2\", \"deviceName\": \"iPhone Simulator\", \"device-orientation\": \"portrait\", \"platform\":\"OS X 10.10\" }'"
  )

  ## now loop through the above array
  for i in "${capabilities[@]}"
  do
    echo "Testing Configuration: $i"
    eval $i
    $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z travis -c -k9 --port 9000
    sleep 5
    grunt protractor:saucelabs
  done

fi
