#!/bin/bash -x
set -e

echo "Running Build & Install"
distro="$(lsb_release -cs)"
sudo apt-get -y update

sudo apt-get -y install curl git debhelper devscripts dh-apparmor dh-python python python-pip python-setuptools python-sphinx

if [ $distro = "bionic" ]; then
  sudo apt-get -y install python3-pip python3-setuptools python3-sphinx
fi

curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -
sudo apt-get -y install nodejs
cd /build/GlobaLeaks
sed -ie 's/key_bits = 2048/key_bits = 512/g' backend/globaleaks/settings.py
sed -ie 's/csr_sign_bits = 512/csr_sign_bits = 256/g' backend/globaleaks/settings.py
rm debian/control backend/requirements.txt

cat >debian/changelog <<EOL
globaleaks (6.6.6) stable; urgency=medium

  * GlobaLeaks CI package

 -- GlobaLeaks software signing key <info@globaleaks.org>  Wed, 30 May 2018 14:19:43 +0200
EOL

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

if [ $distro = "xenial" ] || [ $distro = "stretch" ]; then
  sudo curl http://http.us.debian.org/debian/pool/main/p/python-josepy/python-josepy_1.0.1-1~bpo9+1_all.deb --output /globaleaks/deb/python-josepy_1.0.1-1~bpo9+1_all.deb
  sudo curl http://http.us.debian.org/debian/pool/main/p/python-acme/python-acme_0.22.2-1~bpo9+1_all.deb --output /globaleaks/deb/python-acme_0.22.2-1~bpo9+1_all.deb
fi

sudo ./scripts/install.sh --assume-yes --test
