#!/bin/sh
apt-get install curl git -y
mkdir -p /data/globaleaks
chown travis:travis /data/globaleaks
echo "USE mysql;\nUPDATE user SET password=PASSWORD('globaleaks') WHERE user='root';\nFLUSH PRIVILEGES;\n" | mysql -u root
mysql -e 'create database globaleaks;'
