#!/bin/sh
set -e

# The following script emulates the installation guide:
# <https://github.com/globaleaks/GlobaLeaks/wiki/Installation-guide>

# install globaleaks
dpkg -i globaleaks*.deb || true
apt-get install -fy
