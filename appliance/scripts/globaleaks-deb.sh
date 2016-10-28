#!/bin/sh

cat > /etc/default/globaleaks <<EOL
LOGLEVEL='DEBUG'
NETWORK_SANDBOXING=0                                                                                    
APPARMOR_SANDBOXING=0                                                                                
HOSTS_LIST=127.0.0.1,localhost,192.168.33.10,0.0.0.0
ALLOWED_DST_IP=192.168.33.10
EOL

dpkg --install /vagrant/http/globaleaks*.deb 2>&1
apt-get install -y -f

service globaleaks restart
