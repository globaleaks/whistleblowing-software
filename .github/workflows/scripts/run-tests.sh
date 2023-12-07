#!/bin/bash

set -e

LOGFILE="$GITHUB_WORKSPACE/backend/workingdir/log/globaleaks.log"
ACCESSLOG="$GITHUB_WORKSPACE/backend/workingdir/log/access.log"

function atexit {
  if [[ -f $LOGFILE ]]; then
    cat $LOGFILE
  fi

  if [[ -f $ACCESSLOG ]]; then
    cat $ACCESSLOG
  fi
}

trap atexit EXIT

setupClientDependencies() {
  cd  $GITHUB_WORKSPACE/client  # to install frontend dependencies
  npm install
  grunt instrument-client
}

setupBackendDependencies() {
  cd  $GITHUB_WORKSPACE/backend  # to install backend dependencies
  pip3 install -r requirements/requirements-$(lsb_release -cs).txt
}

setupDependencies() {
  setupClientDependencies
  setupBackendDependencies
}

sudo apt-get update
sudo apt-get install -y tor
npm install -g grunt grunt-cli

pip install coverage

echo "Running backend unit tests"
setupDependencies
cd  $GITHUB_WORKSPACE/backend && coverage run setup.py test

$GITHUB_WORKSPACE/backend/bin/globaleaks -z
sleep 5

echo "Running BrowserTesting locally collecting code coverage"
cd  $GITHUB_WORKSPACE/client && npm test

cd  $GITHUB_WORKSPACE/backend && coverage xml
bash <(curl -Ls https://coverage.codacy.com/get.sh) report -l Python -r  $GITHUB_WORKSPACE/backend/coverage.xml
bash <(curl -Ls https://coverage.codacy.com/get.sh) report -l Javascript -r  $GITHUB_WORKSPACE/client/cypress/coverage/lcov.info
bash <(curl -Ls https://coverage.codacy.com/get.sh) final
