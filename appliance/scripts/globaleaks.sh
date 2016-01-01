#!/bin/sh

set -e

# The following script emulates the installation guide:
# <https://github.com/globaleaks/GlobaLeaks/wiki/Installation-guide>

wget https://deb.globaleaks.org/install-globaleaks.sh
chmod +x install-globaleaks.sh
./install-globaleaks.sh
