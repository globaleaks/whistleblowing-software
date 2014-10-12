#!/bin/sh
sudo apt-get install tor tor-geoipdb
sudo apt-get install nodejs npm
sudo apt-get install equivs devscripts

sudo mk-build-deps -i -r GLBackend/debian/control

sudo -i npm install -g grunt-cli bower
