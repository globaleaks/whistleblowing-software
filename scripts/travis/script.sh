#!/bin/bash
set -e

DO_SUDO() { sudo -i bash -x -c "$@" ; };

DO_SUDO 'cd GLClient/ && node_modules/mocha/bin/mocha -R list tests/glbackend/test_00*'

cd GLBackend
coverage run setup.py test
coveralls || true

# Commented because not fully implemented yet
#if [ "${TRAVIS_REPO_SLUG}" = "globaleaks/GLClient" ]; then
#  cd /data/globaleaks/tests/GLClient
#  git checkout ${TRAVIS_BRANCH} > /dev/null || git checkout HEAD > /dev/null
#  npm install -d
#  grunt unittest
#fi
