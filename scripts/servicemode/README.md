## create-gl-instance.sh

This script is used to create multiple instances of GlobaLeaks on a server.

USAGE: ./servicemode/create-gl-instance.sh options

   This script help in the creation of a new globaleaks instance.

	-d: domain (e.g.: subdomain.domain.tld)        [REQUIRED]

        -p: port (e.g.: 8082)                          [REQUIRED]

        -n: nodebase (e.g.: /var/subdomain.domain.tld) [OPTIONAL]


EXAMPLE:

   ./servicemode/create-gl-instance.sh -d globaleaks.example.org -p 12345 -n /var/globaleaks.example.org

   by issuing this command a new GlobaLeaks instance is created in /var/globaleaks.example.org
   the command does also setup tor for a new Hidden Service; to enable it Tor must be restarted.


   to start/restart the globaleaks instance run: $nodebase/restart-$domain.sh

   e.g.: /var/globaleaks.example.org/restart-globaleaks.example.org.sh
