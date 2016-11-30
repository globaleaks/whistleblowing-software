#!/bin/sh

sudo apt-get -y install dkms make

sudo mount -o loop,ro ~/VBoxGuestAdditions.iso /mnt/
sudo /mnt/VBoxLinuxAdditions.run || :

ln -sf /opt/VBoxGuestAdditions-$VERSION/lib/VBoxGuestAdditions /usr/lib/VBoxGuestAdditions

sudo umount /mnt/
rm -f ~/VBoxGuestAdditions.iso
