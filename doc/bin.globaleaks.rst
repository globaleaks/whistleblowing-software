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

**-h, --help**
    Show this help message with default values and exits

**-n, --nodaemon**
    Don't daemonize

**-l LOGLEVEL, --loglevel=LOGLEVEL**
    Set log level [default: `CRITICAL`]

**-i IP, --ip=IP**
    IP address(s) used for listening [default: `127.0.0.1`]

**-p PORT, --port=PORT**
    TCP port used for listening [default: `8082`]

**-a HOST_LIST, --accept-host=HOST_LIST**
    Specify a list comma separated of hostname acceptable
    by the HTTP server. If some hosts are specified,
    defaults are not more included in the allowed list)
    [default: `127.0.0.1`, localhost]

**-s SOCKS_HOST, --socks-host=SOCKS_HOST**
    Set Socks host to use for Tor [default: `127.0.0.1`]

**-r SOCKS_PORT, --socks-port=SOCKS_PORT**
    Set Socks port to use for Tor [default: `9050`]

**-t SIDE_CHANNELS_GUARD, --side-channels-guard=SIDE_CHANNELS_GUARD**
    Security guard time to wich uniform request times to
    reduce side channels analysis (ms)

**-d, --disable-mail-torification**
    Disable mail torification

**-f, --disable-mail-notification**
    Disable mail notification

**-b, --disable-backend-exception-notification**
    Disable backend_exception_notification

**-e, --disable-client-exception-notification**
    Disable_client_exception_notification

**-m DISK_ALARM_THRESHOLD, --disks-alarm-threshold=DISK_ALARM_THRESHOLD**
    Takes 1, 2, 3, set disk alarm threshold [default: `0`]

**-x TOR_DIR, --tor-dir=TOR_DIR**
    Tor directory, acquire hidden service and set onion.to proxy [default: None]

**-u USER, --user=USER**
    Set the user to run as [default: current_user]

**-g GROUP, --group=GROUP**
    Set the group to run as [default: current_user]

**-w WORKING_PATH, --working-path=WORKING_PATH**
    Set the backend working directory

**-c, --start-clean**
    Start a clean globaleks install [default: False]

**-k KILL, --kill=KILL**
    Signal to send to the current globaleaks process (if exists)

**-W, --skip-wizard**
    Skip globaleaks installation wizard' [default: False]

**-A API_PREFIX, --api-prefix=API_PREFIX**
    Specify an API prefix

**-C CLIENT_PATH, --client-path=CLIENT_PATH**
    Specify client path

**-P, --disable-swap**
    Disable process swap [default: `False`]

**-R RAMDISK, --ramdisk=RAMDISK**
    Optionally specify a path used as ramdisk storage

**-z DEVELOPER_NAME, --devel-mode=DEVELOPER_NAME**
    Hack some configs, specify your name to receive
    personalized exceptions

**-o, --orm-debug**
    Enable ORM debugging (AVAILABLE ONLY IN DEVEL MODE)

**-j, --request-log**
    Enable request/response logging (AVAILABLE ONLY IN DEVEL MODE)

**-S, --request-stats**
    Enable requests timing stats (AVAILABLE ONLY IN DEVEL MODE)

**-v, --version**
    Show the version of the software

Security
--------

In order to provide some protection for the system from the globaleaks process, this program should be run in an App Armor sandbox. Additionally, the user that owns the process is 'globaleaks', you can use the **--user** argument to specify which to run the program as.

Configuration
---------------

Normally, globaleaks is configured by its installation script to run as a service
on the system. If you need to change the arguments passed to the service change 
`globaleaks.init` at your own risk.

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
Starting GlobaLeaks
Usage: globaleaks [options]
