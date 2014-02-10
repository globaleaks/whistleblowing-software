#!/bin/sh
echo "USE mysql;\nUPDATE user SET password=PASSWORD('globaleaks') WHERE user='root';\nFLUSH PRIVILEGES;\n" | mysql -u root
mysql -e 'create database globaleaks;'
