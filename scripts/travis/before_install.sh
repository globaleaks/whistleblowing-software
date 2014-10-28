#!/bin/bash

# Add tor repository.
sudo add-apt-repository \
    "deb http://deb.torproject.org/torproject.org $(lsb_release -s -c) main"
gpg --keyserver x-hkp://pool.sks-keyservers.net --recv-keys 0x886DDD89
gpg --export A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89 | sudo apt-key add -

# Add apt repository
sudo add-apt-repository -y ppa:chris-lea/node.js

sudo apt-get update -qq
