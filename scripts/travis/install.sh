#!/bin/sh

# Add tor repository.
add-apt-repository "deb http://deb.torproject.org/torproject.org $(lsb_release -s -c) main" -y
gpg --keyserver x-hkp://pool.sks-keyservers.net --recv-keys 0x886DDD89
gpg --export A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89 | sudo apt-key add -

sudo apt-get update -qq
sudo apt-get install tor tor-geoipdb
sudo apt-get install nodejs npm
sudo apt-get install equivs devscripts
