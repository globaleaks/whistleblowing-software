#!/bin/bash -x
set -e

echo "Running Build & Install"
distro="$(lsb_release -cs)"
sudo apt-get update -y
sudo apt-get install -y curl git debhelper devscripts dh-apparmor dh-python python python-pip python-setuptools python-sphinx
curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -
sudo apt-get install -y nodejs
cd /build/GlobaLeaks
sed -ie 's/key_bits = 2048/key_bits = 512/g' backend/globaleaks/settings.py
sed -ie 's/csr_sign_bits = 512/csr_sign_bits = 256/g' backend/globaleaks/settings.py
rm debian/control backend/requirements.txt
cp debian/controlX/control.$distro debian/control
cp backend/requirements/requirements-$distro.txt backend/requirements.txt
cd client
npm install grunt-cli
npm install -d
./node_modules/.bin/grunt build
cd ..
debuild -i -us -uc -b
sudo mkdir -p /globaleaks/deb/
sudo cp ../globaleaks*deb /globaleaks/deb/
sudo ./scripts/install.sh --assume-yes --test
