Upgrade Guide
=============
Regular Update
--------------
To safely upgrade a GlobaLeaks installation please proceed with a backup of your setup by following the :doc:`Backup and restore </user/admin/BackupAndRestore>` guide.

This is necessary so that if something goes wrong and you need to rollback, you will be able to just uninstall the current package, then install the same version of globaleaks that was previously installed and working.

In order to update GlobaLeaks perform the following commands:

.. code::

   apt-get update && apt-get install globaleaks

Upgrade of the Distribution Version
-----------------------------------
For security and stability reasons it is recommended to not perform a distribution upgrade.

GlobaLeaks could be instead easily migrated to a new up-to-date Debian system with the following recommended instructions:

- Create an archive backup of /var/globaleaks
- Instantiate the lates Debian available.
- Log on the new server and extract the backup in /var/globaleaks
- Follow the :doc:`Installation Guide </setup/InstallationGuide>`; GlobaLeaks while installing will recognize the presence of an existing data directory and will use it.

In Case of Errors
-----------------
The above commands should allow you to perform regular updates. In some conditions due to special updates, it could be possible that those commands result in a failure. Consult this page for knowing specific FAQs on precise failures.

In case you do not find any specific documented solution for your failure, you could run the GlobaLeaks install script. The installation script in fact is designed to allow the update of GlobaLeaks and it includes fixes for the most common issue.

To run the install script for updating globaleaks perform the following commands:

.. code::

   wget https://deb.globaleaks.org/install-globaleaks.sh
   chmod +x install-globaleaks.sh
   ./install-globaleaks.sh
