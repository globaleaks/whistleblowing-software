#!/bin/sh
sudo -i bash -x -c 'mkdir -p /data/globaleaks'
sudo -i bash -x -c 'chown travis:travis /data/globaleaks'
sudo -i bash -x -c 'apt-get install curl git -y'
echo "USE mysql;\nUPDATE user SET password=PASSWORD('globaleaks') WHERE user='root';\nFLUSH PRIVILEGES;\n" | mysql -u root
mysql -e 'create database globaleaks;'
