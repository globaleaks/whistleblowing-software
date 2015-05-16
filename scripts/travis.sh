#!/bin/bash

set -e

if [ "$TEST_SUITE" = "units" ]; then

  cd $TRAVIS_BUILD_DIR/backend  # to run backend tests
  coverage run setup.py test
  coveralls || true
  cd $TRAVIS_BUILD_DIR/client  # to test backend handlers
  bower install && grunt build --resource master
  $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z travis
  node_modules/mocha/bin/mocha -R list tests/glbackend/test_00* --timeout 4000
  $TRAVIS_BUILD_DIR/scripts/travis_saucelabs.sh

elif [ "$TEST_SUITE" = "end2end" ]; then

  declare -a capabilities=(
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"firefox\", \"platform\":\"Linux\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"firefox\", \"platform\":\"OS X 10.10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"firefox\", \"version\":\"36.0\", \"platform\":\"Windows 8.1\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"firefox\", \"version\":\"37.0\", \"platform\":\"Windows 8.1\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"chrome\", \"platform\":\"Linux\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"chrome\", \"platform\":\"OS X 10.10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"chrome\", \"version\":\"37.0\", \"platform\":\"Windows 8.1\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"chrome\", \"version\":\"38.0\", \"platform\":\"Windows 8.1\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"chrome\", \"version\":\"39.0\", \"platform\":\"Windows 8.1\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"chrome\", \"version\":\"40.0\", \"platform\":\"Windows 8.1\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"chrome\", \"version\":\"41.0\", \"platform\":\"Windows 8.1\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"chrome\", \"version\":\"42.0\", \"platform\":\"Windows 8.1\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"safari\", \"platform\":\"OS X 10.10\"}'"
    "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"internet explorer\", \"version\":\"11\", \"platform\":\"Windows 8.1\"}'"
  )

  ## now loop through the above array
  for i in "${capabilities[@]}"
  do
    eval $i
    $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z travis -c -k9 --port 8080
    sleep 1
    grunt protractor:saucelabs
  done

fi
