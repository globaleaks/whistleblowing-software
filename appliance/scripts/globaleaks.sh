#!/bin/bash
# The following script emulates the installation guide:
# <https://github.com/globaleaks/GlobaLeaks/wiki/Installation-guide>
set -e

# XXX. python-cryptography is not available on ubuntu trusty,
# so I am downloading it from debian jessie repositories.
wget http://ftp.de.debian.org/debian/pool/main/p/python-cryptography/python-cryptography_0.6.1-1_amd64.deb
dpkg -i python-cryptography* || true
apt install -fy

# XXX. Temporairly disable iptables, as it currently locks me out from ssh.
apt install -y iptables
mv /sbin/iptables /sbin/iptables.1
ln -s /bin/true /sbin/iptables

# install globaleaks
dpkg -i globaleaks* || true
apt install -fy

# XXX. This should be moved in {pre,post}{inst,rm} debian scripts, or either
# handled directly inside GlobaLeaks.
cat <<EOF >> /etc/tor/torrc

# GlobaLeaks Configuration.
VirtualAddrNetwork 10.23.47.0/10
AutomapHostsOnResolve 1
TransPort 9040
TransListenAddress 127.0.0.1
DNSPort 5353
DNSListenAddress 127.0.0.1
HiddenServiceDir /var/globaleaks/torhs/
HiddenServicePort 80 127.0.0.1:8082
EOF
## finally, restart tor in order to reload /etc/torrc.
## XXX. Supposedly, if we remove this line every machine will have a different hidden service.
## What should the default be?
service tor restart
