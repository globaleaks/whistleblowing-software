#!/bin/bash

set -e

# build the client
cd $TRAVIS_BUILD_DIR/client
bower install
grunt build

if [ "$GLTEST" = "false" ]; then

  cd $TRAVIS_BUILD_DIR/backend
  coverage run setup.py test
  coveralls || true
  $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z travis
  $TRAVIS_BUILD_DIR/client/node_modules/mocha/bin/mocha -R list $TRAVIS_BUILD_DIR/client/tests/api/test_00* --timeout 4000

elif [ "$GLTEST" = "loader-only" ]; then

  echo "Mocha test: $GLTEST"
  grunt test-loader-saucelabs

else

  echo "Protractor End2End test: $GLTEST"

  $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z travis -c -k9 --port 8080
  grunt protractor:saucelabs

fi
