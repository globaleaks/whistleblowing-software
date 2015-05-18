#!/bin/bash

set -e

# build the client
cd $TRAVIS_BUILD_DIR/client  # to test backend handlers
bower install && grunt build

if [ "$TEST_E2E" = "false" ]; then

  cd $TRAVIS_BUILD_DIR/backend  # to run backend tests
  coverage run setup.py test
  coveralls || true
  $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z travis
  $TRAVIS_BUILD_DIR/client/node_modules/mocha/bin/mocha -R list $TRAVIS_BUILD_DIR/client/tests/glbackend/test_00* --timeout 4000

else

  echo "Protractor End2End test: $TEST_E2E"

  $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z travis -c -k9 --port 8080
  grunt protractor:saucelabs

fi
