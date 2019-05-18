=======================
Backup and restore
=======================
The following bash script could be used in order to perform a backup manually:

.. code::

   #!/bin/sh
   set -e

   if [ -d "/var/globaleaks" ]; then
     timestamp=$(date +%s)
     version=`dpkg -s globaleaks | grep '^Version:' | cut -d ' ' -f2`
     filepath=/var/globaleaks/backups/globaleaks-$version-$timestamp.tar.gz
     echo "Creating backup of /var/globaleaks in $filepath"
     mkdir -p /var/globaleaks/backups
     chown globaleaks:globaleaks /var/globaleaks/backups
     tar --exclude='/var/globaleaks/backups' -zcvf $filepath /var/globaleaks
   fi

After the completion of the command you willfind  a tar.gz archive within the /var/globaleaks/backups.
The file will have the format: globaleaks-$version-$timestamp.tar.gz

GlobaLeaks does automatically perform a backup at each platform update and the backup is kept under data
retention policy and is deleted 15 days after the update.

To restore an existing backup:
 - be sure globaleaks is not running; globaleaks can be shut down with "service globaleaks stop";
 - identify the version of globaleaks required for restoring globaleaks. the version is written in the backup filename;
 - extract the content of the archive in /var/globaleaks with the command tar -zxvf backup.tar.gz
 - install the required version of globaleaks with: apt-get install globaleaks=version (e.g. globaleaks=3)
