#!/bin/bash

set -e

DO_SUDO() { sudo -i bash -x -c "$@" ; };

./scripts/build-testing-package.sh ${TRAVIS_BRANCH} ${TRAVIS_BRANCH}
exit

# The following emulates the installation guide:
#   https://github.com/globaleaks/GlobaLeaks/wiki/Installation-guide
DO_SUDO 'mkdir -p /data/globaleaks/deb/'
DO_SUDO 'cp /data/globaleaks/GLBackend_tmp/glbackend_build/deb_dist/globaleaks*deb /data/globaleaks/deb/'
DO_SUDO 'chmod +x /data/globaleaks/GlobaLeaks/scripts/install-ubuntu.sh'
DO_SUDO 'TRAVIS=true /data/globaleaks/GlobaLeaks/scripts/install-ubuntu.sh'

DO_SUDO 'echo "VirtualAddrNetwork 10.23.47.0/10" >> /etc/tor/torrc'
DO_SUDO 'echo "AutomapHostsOnResolve 1" >> /etc/tor/torrc'
DO_SUDO 'echo "TransPort 9040" >> /etc/tor/torrc'
DO_SUDO 'echo "TransListenAddress 127.0.0.1" >> /etc/tor/torrc'
DO_SUDO 'echo "DNSPort 5353" >> /etc/tor/torrc'
DO_SUDO 'echo "DNSListenAddress 127.0.0.1" >> /etc/tor/torrc'
DO_SUDO 'echo "HiddenServiceDir /var/globaleaks/torhs/" >> /etc/tor/torrc'
DO_SUDO 'echo "HiddenServicePort 80 127.0.0.1:8082" >> /etc/tor/torrc'
DO_SUDO '/etc/init.d/tor restart'

# DO_SUDO "[db]" > /etc/globaleaks'
# DO_SUDO "type: mysql" >> /etc/globaleaks'
# DO_SUDO "username: root" >> /etc/globaleaks'
# DO_SUDO "password: globaleaks" >> /etc/globaleaks'
# DO_SUDO "hostname: localhost" >> /etc/globaleaks'
# DO_SUDO "name: globaleaks" >> /etc/globaleaks'

# damn travis seems to have problm on /dev/shm, making a special configuration for this
DO_SUDO 'mkdir /var/globaleaks/ramdisk && \
         chown globaleaks:globaleaks /var/globaleaks/ramdisk && \
         chmod 700 /var/globaleaks/ramdisk'
DO_SUDO 'sed -i "s/RAM_DISK=\/dev\/shm\/globaleaks\//RAM_DISK=\/var\/globaleaks\/ramdisk\//g" /etc/default/globaleaks'
DO_SUDO 'TRAVIS=true/etc/init.d/globaleaks restart'

git clone https://github.com/globaleaks/GLClient /data/globaleaks/GlobaLeaks_UT
cd /data/globaleaks/GlobaLeaks_UT && (git checkout ${TRAVIS_BRANCH} > /dev/null || git checkout HEAD > /dev/null)
DO_SUDO 'cd /data/globaleaks/GlobaLeaks_UT && npm install -d'
DO_SUDO 'cd /data/globaleaks/GlobaLeaks_UT && node_modules/mocha/bin/mocha -R list tests/glbackend/test_00*'

git clone https://github.com/globaleaks/GLBackend /data/globaleaks/tests/GLBackend
cd /data/globaleaks/tests/GLBackend
git checkout ${TRAVIS_BRANCH} > /dev/null || git checkout HEAD > /dev/null

git clone https://github.com/globaleaks/GLClient /data/globaleaks/tests/GLClient
cd /data/globaleaks/tests/GLClient
git checkout ${TRAVIS_BRANCH} > /dev/null || git checkout HEAD > /dev/null

if [ "${TRAVIS_REPO_SLUG}" = "globaleaks/GLBackend" ]; then
  pip install coverage
  pip install coveralls
  coverage run $(which trial) globaleaks
  coveralls || true
fi

# Commented because not fully implemented yet
#if [ "${TRAVIS_REPO_SLUG}" = "globaleaks/GLClient" ]; then
#  cd /data/globaleaks/tests/GLClient
#  git checkout ${TRAVIS_BRANCH} > /dev/null || git checkout HEAD > /dev/null
#  npm install -d
#  grunt unittest
#fi
