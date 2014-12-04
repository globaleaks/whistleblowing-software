Globaleaks User Commands: bin/globaleaks
========================================

Globaleaks aims to create a worldwide, anonymous, censorship-resistant,
distributed whistleblowing platform.

Synopsis
--------
Usage: *globaleaks* [options]


Description
-----------
Start the globaleaks server.

**-v, --version**
    Show the version of the software.

**-n, --nodaemon**
    Don't daemonize [default: `False`]

**-l LOGLEVEL, --loglevel=LOGLEVEL**
    Set log level [default: `CRITICAL`]

**-i IP, --ip=IP**
    IP address(s) used for listening [default: `127.0.0.1`]

**-p PORT, --port=PORT**
    TCP port used for listening [default: `8082`]

**-a HOST_LIST, --accept-host=HOST_LIST**
    Specify a list comma separated of hostnames acceptable by the HTTP server.
    (If some hosts are specified, defaults are not more included in the allowed
    list). [default: `127.0.0.1`]

**-o SOCKS_HOST, --socks-host=SOCKS_HOST**
    Set Socks host to use for Tor [default: `127.0.0.1`]

**-P SOCKS_PORT, --socks-port=SOCKS_PORT**
    Set Socks port to use for Tor [default: `9050`]

**-D TOR_DIR, --tor-dir=TOR_DIR**
    Tor directory, acquire hidden service and set onion.to proxy [default: `None`]

**-R RAMDISK, --ramdisk=RAMDISK**
    Optionally specify a path used by GnuGP operations [default: `absent`].

**--loglevel=VERBOSITY**
    Set log verbosity. Values for verbosity are **DEBUG**, **INFO**, **CRITICAL**,
    **ERROR**. [default: `CRITICAL`].

**-w WORKING_PATH, --working-path=WORKING_PATH**
   set the glbackend working directory [default: `/var/globaleaks`]

**--working-dir=DIR**
    Directory hosting GlobaLeaks data.

**-h, --help**
    Display the full list of options.


Security
--------

TODO

Configuration
---------------

TODO

Logs
----

GlobaLeaks does have different kind of log files and logging priority to
facilitate the debugging at various level.

The log files are stored in the working dir (by default **/var/globaleaks**),
under the "log" directory. You can choose the working dir using the command line
option **--working-path**, and tune log verbosity using
**--loglevel**. *Globaleaks*  will write the following log files:

* `globaleaks.log` - Main application log
* `twistd.log` - Logging/debugging HTTP requests and Twisted related issue

Plus, globaleaks will log every json request into the `jsondump/` directory.


Bugs
----

Globaleaks bugs can be reported either via mail to `info@globaleaks.org` or
directly to the bug tracker at <https://github.com/globaleaks/GlobaLeaks/issues>.
