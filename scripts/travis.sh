#!/bin/bash

set -e

# build the client
cd $TRAVIS_BUILD_DIR/client  # to test backend handlers
bower install && grunt build

if [ "$TEST_SUITE" = "units" ]; then

  cd $TRAVIS_BUILD_DIR/backend  # to run backend tests
  coverage run setup.py test
  coveralls || true
  $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z travis
  $TRAVIS_BUILD_DIR/client/node_modules/mocha/bin/mocha -R list $TRAVIS_BUILD_DIR/client/tests/glbackend/test_00* --timeout 4000

else

  if [ "$TEST_SUITE" = "end2end-01" ]; then
    export SELENIUM_BROWSER_CAPABILITIES='{"browserName":"firefox", "platform":"Linux"}'
  elif [ "$TEST_SUITE" = "end2end-02" ]; then
    export SELENIUM_BROWSER_CAPABILITIES='{"browserName":"firefox", "platform":"OS X 10.10"}'
  elif [ "$TEST_SUITE" = "end2end-03" ]; then
    export SELENIUM_BROWSER_CAPABILITIES='{"browserName":"firefox", "version":"36.0", "platform":"Windows 8.1"}'
  elif [ "$TEST_SUITE" = "end2end-04" ]; then
    export SELENIUM_BROWSER_CAPABILITIES='{"browserName":"firefox", "version":"37.0", "platform":"Windows 8.1"}'
  elif [ "$TEST_SUITE" = "end2end-05" ]; then
    export SELENIUM_BROWSER_CAPABILITIES='{"browserName":"chrome", "platform":"Linux"}'
  elif [ "$TEST_SUITE" = "end2end-06" ]; then
    export SELENIUM_BROWSER_CAPABILITIES='{"browserName":"chrome", "platform":"OS X 10.10"}'
  elif [ "$TEST_SUITE" = "end2end-07" ]; then
    export SELENIUM_BROWSER_CAPABILITIES='{"browserName":"chrome", "version":"37.0", "platform":"Windows 8.1"}'
  elif [ "$TEST_SUITE" = "end2end-08" ]; then
    export SELENIUM_BROWSER_CAPABILITIES='{"browserName":"chrome", "version":"38.0", "platform":"Windows 8.1"}'
  elif [ "$TEST_SUITE" = "end2end-09" ]; then
    export SELENIUM_BROWSER_CAPABILITIES='{"browserName":"chrome", "version":"39.0", "platform":"Windows 8.1"}'
  elif [ "$TEST_SUITE" = "end2end-10" ]; then
    export SELENIUM_BROWSER_CAPABILITIES='{"browserName":"chrome", "version":"40.0", "platform":"Windows 8.1"}'
  elif [ "$TEST_SUITE" = "end2end-11" ]; then
    export SELENIUM_BROWSER_CAPABILITIES='{"browserName":"chrome", "version":"41.0", "platform":"Windows 8.1"}'
  elif [ "$TEST_SUITE" = "end2end-12" ]; then
    export SELENIUM_BROWSER_CAPABILITIES='{"browserName":"chrome", "version":"42.0", "platform":"Windows 8.1"}'
  elif [ "$TEST_SUITE" = "end2end-13" ]; then
    export SELENIUM_BROWSER_CAPABILITIES='{"browserName":"safari", "platform":"OS X 10.10"}'
  elif [ "$TEST_SUITE" = "end2end-14" ]; then
    export SELENIUM_BROWSER_CAPABILITIES='{"browserName":"internet explorer", "version":"11", "platform":"Windows 8.1"}'
  fi

  $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z travis -c -k9 --port 8080
  grunt protractor:saucelabs

fi
