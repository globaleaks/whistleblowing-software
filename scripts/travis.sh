#!/bin/bash

set -e

if [ "$GLTEST" = "unit" ]; then

  cd $TRAVIS_BUILD_DIR/backend
  coverage run setup.py test
  coveralls || true
  $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z travis
  $TRAVIS_BUILD_DIR/client/node_modules/mocha/bin/mocha -R list $TRAVIS_BUILD_DIR/client/tests/api/test_00* --timeout 4000

elif [ "$GLTEST" = "browserchecks" ]; then

  echo "Mocha test: $GLTEST"
  grunt test-browserchecks-saucelabs

else

  echo "Protractor End2End test: $GLTEST"

  declare -a capabilities=(
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"firefox\", \"version\":\"37.0\", \"platform\":\"Windows 8.1\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"chrome\", \"version\":\"42.0\", \"platform\":\"Windows 8.1\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"safari\", \"version\":\"8\", \"platform\":\"OS X 10.10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"internet explorer\", \"version\":\"11\", \"platform\":\"Windows 8.1\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"android\", \"version\": \"5.1\", \"deviceName\": \"Android Emulator\", \"platform\": \"Linux\", \"platform\":\"OS X 10.10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\": \"iphone\", \"version\": \"8.2\", \"deviceName\": \"iPhone Simulator\", \"device-orientation\": \"portrait\", \"platform\":\"OS X 10.10\" }'"
  )

  ## now loop through the above array
  for i in "${capabilities[@]}"
  do
    eval $i
    $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z travis -c -k9 --port 9000
    sleep 3
    grunt protractor:saucelabs
  done

fi
