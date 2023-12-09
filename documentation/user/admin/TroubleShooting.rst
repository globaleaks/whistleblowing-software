===============
Troubleshooting
===============
Issues and Bug Reporting
------------------------
If you encounter any issue and you are not able to to run GlobaLeaks:

- Be sure to strictly follow the Installation Guide for installation
- Be sure to satisfy the Technical Requirements for hardware and operating system version.
- Search on the support forum to check if a user has already encountered your issue: https://github.com/orgs/globaleaks/discussions
- Report the issue on the official software ticking system: https://github.com/globaleaks/GlobaLeaks/issues

Useful Debugging Commands
-------------------------
Depending on your setup. There are a few things that are usually the first things to check to see if GlobaLeaks is working.

- Is the service running?

::

  service globaleaks status

- Is the service responding on the loopback interface?

::

  curl -kis -vvv localhost:8433

- Is the service listening on external interfaces?

::

  netstat -tap

- Are exceptions being generated?

::

  less /var/globleaks/log/globaleaks.log


Log Files
---------
There are a few useful logs and corresponding log files when GlobaLeaks is installed.

**GlobaLeaks process:**

::

  /var/globaleaks/log/globaleaks.log


The verbosity is configurable via the web interface of the software inside Advanced Settings.
