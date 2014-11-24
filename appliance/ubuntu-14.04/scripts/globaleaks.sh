#!/bin/bash
# The following script emulates the installation guide:
# <https://github.com/globaleaks/GlobaLeaks/wiki/Installation-guide>
set -e

# XXX. python-storm 0.20 is not available on ubuntu trusty.
# A debian package is available at <http://mentors.debian.net/package/storm>

# XXX. python-cryptography is not available on ubuntu trusty,
# so I am downloading it from debian jessie repositories.
wget http://ftp.de.debian.org/debian/pool/main/p/python-cryptography/python-cryptography_0.6.1-1_amd64.deb
dpkg -i python-cryptography* || true
apt install -fy

# install globaleaks
dpkg -i globaleaks* || true
apt install -fy
