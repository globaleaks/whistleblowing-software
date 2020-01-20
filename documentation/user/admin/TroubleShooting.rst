===============
Troubleshooting
===============

Issues and bug reporting
------------------------
If you encounter any issue and you are not able to to run GlobaLeaks h

- Be sure to strictly follow the Installation Guide for installation
- Be sure to satisfy the Technical Requirements for hardware and operating system version.
- Search on the support forum to check if a user has already encountered your issue: https://forum.globaleaks.org
- Report the issue on the official software ticking system: https://github.com/globaleaks/GlobaLeaks/issues

Useful debugging commands
-------------------------
Depending on your setup. There are a few things that are usually the first things to check to see if GlobaLeaks is working.

- Is the service running?

::

  service globaleaks status

- Is the service responding on the loopback interface?

::

  curl -vvv localhost:8082

- Is the service listening on external interfaces? Is Tor2Web service listening on 443?

::

  netstat -tap

- Are exceptions being generated?

::

  less /var/globleaks/logs/globaleaks.log


Log files
---------
There are a few useful logs and corresponding log files when GlobaLeaks is installed.

**GlobaLeaks process:**

::

  /var/globaleaks/logs/globaleaks.log


The verbosity is configurable via the web interface of the software inside Advanced Settings.


**Tor:**

::

  /var/log/tor/log Iptables: /var/log/syslog AppArmor: /var/log/kern.log
