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
HOSTS_LIST=127.0.0.1,localhost,192.168.33.10,0.0.0.0
ALLOWED_DST_IP=192.168.33.10
EOL


config.vm.network "private_network", ip: "192.168.33.10"
