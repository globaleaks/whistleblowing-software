#!/bin/bash

# install the backported kernel
apt-get update
apt-get install -y linux-image-generic-lts-raring linux-headers-generic-lts-raring

# reboot
echo "Rebooting the machine..."
reboot
sleep 60
