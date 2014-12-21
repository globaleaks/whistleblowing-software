## create-gl-instance.sh

This script is used to create multiple instances of GlobaLeaks on a server.

USAGE: ./servicemode/create-gl-instance.sh options

   This script help in the creation of a new globaleaks instance.

        -d: domain (e.g.: subdomain.domain.tld)

        -p: port (e.g.: 8082)

EXAMPLE:

   ./servicemode/create-gl-instance.sh -d globaleaks.example.org -p 12345

   by issuing this command a new GlobaLeaks instance is created in /var/globaleaks/globaleaks.example.org
   the command does also setup Tor for a new Hidden Service; to enable it Tor must be restarted.

   to start/restart the globaleaks instance run: /var/globaleaks/globaleaks.example.org/restart.sh

   e.g.: /var/globaleaks/globaleaks.example.org/restart.sh
