Installation Guide
==================
The following is intended to guide you through the installation of GlobaLeaks.

Before starting the installation, make sure that your system satisfy the :doc:`Requirements </gettingstarted/Requirements>`.

.. WARNING::
  GlobaLeaks is built to give the best technical anonimity to the Whistleblower.
  In addition the software with specific configurations enables the possibility to protect the identity of the platform administrator and the server's location but this requires advanced setup procedures not considered in this simplified installation guide.
  By executing the commands below your IP address and the location of your system could be tracked by the network providers and as well our systems will be receiving the same information in order to satisfy the provisioning of the software.

**Install GlobaLeaks**

In order to install GlobaLeaks run the following commands:

.. code:: sh

  wget https://deb.globaleaks.org/install-globaleaks.sh
  chmod +x install-globaleaks.sh
  ./install-globaleaks.sh


You may install GlobaLeaks using Docker. Therefore check out the `docker` directory in our GitHub repository.

At the end of the installation follow the instruction provided that should guide through accessing the :doc:`Platform wizard </setup/PlatformWizard>`.
