#!/bin/sh

set -e

# The following script emulates the installation guide:
# <https://github.com/globaleaks/GlobaLeaks/wiki/Installation-guide>

wget https://deb.globaleaks.org/install-globaleaks.sh
chmod +x install-globaleaks.sh
./install-globaleaks.sh


cat > /etc/default/globaleaks <<EOL
line 1, LOGLEVEL='DEBUG'
line 2, NETWORK_SANDBOXING=0
line ...
EOL
