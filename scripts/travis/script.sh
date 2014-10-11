#!/bin/sh

set -e

sudo -i bash -x -c 'mkdir -p /data/globaleaks/tests'
sudo -i bash -x -c 'chown travis:travis /data/globaleaks -R'

git clone https://github.com/globaleaks/GlobaLeaks /data/globaleaks/GlobaLeaks
cd /data/globaleaks/GlobaLeaks
git checkout ${TRAVIS_BRANCH} > /dev/null || git checkout HEAD > /dev/null
/data/globaleaks/GlobaLeaks/scripts/build-testing-package.sh -c${TRAVIS_BRANCH} -b${TRAVIS_BRANCH}
# the following is the emulation of the installation guide:
#   https://github.com/globaleaks/GlobaLeaks/wiki/Installation-guide
sudo -i bash -x -c 'apt-get update -y'
sudo -i bash -x -c 'apt-get install python-software-properties -y'
sudo -i bash -x -c 'add-apt-repository "deb http://deb.torproject.org/torproject.org $(lsb_release -s -c) main" -y'
sudo -i bash -x -c 'gpg --keyserver x-hkp://pool.sks-keyservers.net --recv-keys 0x886DDD89'
sudo -i bash -x -c 'gpg --export A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89 | sudo apt-key add -'
sudo -i bash -x -c 'apt-get update'
sudo -i bash -x -c 'apt-get install tor tor-geoipdb -y'
sudo -i bash -x -c 'mkdir -p /data/globaleaks/deb/'
sudo -i bash -x -c 'cp /data/globaleaks/GLBackend_tmp/glbackend_build/deb_dist/globaleaks*deb /data/globaleaks/deb/'
sudo -i bash -x -c 'chmod +x /data/globaleaks/GlobaLeaks/scripts/install-ubuntu.sh'
sudo TRAVIS=true -i bash -x -c '/data/globaleaks/GlobaLeaks/scripts/install-ubuntu.sh'
sudo -i bash -x -c 'echo "VirtualAddrNetwork 10.23.47.0/10" >> /etc/tor/torrc'
sudo -i bash -x -c 'echo "AutomapHostsOnResolve 1" >> /etc/tor/torrc'
sudo -i bash -x -c 'echo "TransPort 9040" >> /etc/tor/torrc'
sudo -i bash -x -c 'echo "TransListenAddress 127.0.0.1" >> /etc/tor/torrc'
sudo -i bash -x -c 'echo "DNSPort 5353" >> /etc/tor/torrc'
sudo -i bash -x -c 'echo "DNSListenAddress 127.0.0.1" >> /etc/tor/torrc'
sudo -i bash -x -c 'echo "HiddenServiceDir /var/globaleaks/torhs/" >> /etc/tor/torrc'
sudo -i bash -x -c 'echo "HiddenServicePort 80 127.0.0.1:8082" >> /etc/tor/torrc'
sudo -i bash -x -c '/etc/init.d/tor restart'
#sudo -i bash -x -c 'echo "[db]" > /etc/globaleaks'
#sudo -i bash -x -c 'echo "type: mysql" >> /etc/globaleaks'
#sudo -i bash -x -c 'echo "username: root" >> /etc/globaleaks'
#sudo -i bash -x -c 'echo "password: globaleaks" >> /etc/globaleaks'
#sudo -i bash -x -c 'echo "hostname: localhost" >> /etc/globaleaks'
#sudo -i bash -x -c 'echo "name: globaleaks" >> /etc/globaleaks'
# damn travis seems to have problm on /dev/shm, making a special configuration for this
sudo -i bash -x -c 'mkdir /var/globaleaks/ramdisk && chown globaleaks:globaleaks /var/globaleaks/ramdisk && chmod 700 /var/globaleaks/ramdisk'
sudo -i bash -x -c 'sed -i "s/RAM_DISK=\/dev\/shm\/globaleaks\//RAM_DISK=\/var\/globaleaks\/ramdisk\//g" /etc/default/globaleaks'
sudo TRAVIS=true -i bash -x -c '/etc/init.d/globaleaks restart'
sleep 10

git clone https://github.com/globaleaks/GLClient /data/globaleaks/GlobaLeaks_UT
cd /data/globaleaks/GlobaLeaks_UT && (git checkout ${TRAVIS_BRANCH} > /dev/null || git checkout HEAD > /dev/null)
sudo -i bash -x -c 'add-apt-repository ppa:chris-lea/node.js -y'
sudo -i bash -x -c 'apt-get update -y'
sudo -i bash -x -c 'apt-get install nodejs -y'
sudo -i bash -x -c 'cd /data/globaleaks/GlobaLeaks_UT && npm install -d'
sudo -i bash -x -c 'cd /data/globaleaks/GlobaLeaks_UT && node_modules/mocha/bin/mocha -R list tests/glbackend/test_00*'

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
