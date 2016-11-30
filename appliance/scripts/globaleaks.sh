#!/bin/sh

set -e

# The following script emulates the installation guide:
# <https://github.com/globaleaks/GlobaLeaks/wiki/Installation-guide>

wget https://deb.globaleaks.org/install-globaleaks.sh
chmod +x install-globaleaks.sh
yes | ./install-globaleaks.sh

cat > /etc/default/globaleaks <<EOL
LOGLEVEL='DEBUG'
NETWORK_SANDBOXING=0
APPLICATION_SANDBOXING=0
EOL
