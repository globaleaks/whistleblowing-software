.. _introduction:

Introduction
============

txtorcon is an implementation of the `control-spec
<https://gitweb.torproject.org/torspec.git/blob/HEAD:/control-spec.txt>`_
for `Tor <https://www.torproject.org/projects/projects.html.en>`_
using the `Twisted <https://twistedmatrix.com/trac/>`_ networking
library for `Python <http://python.org/>`_ (*supports Py2, PyPy and
Py3*).

**txtorcon gives you a live view of all Tor state and the ability to
control most aspects of Tor's operation**. With txtorcon you can
launch tor; connect to already-running tor instances; use tor as a
client (via SOCKS5); set up (onion) services over tor; change all
aspects of configuration; track live state (active circuits and
streams, etc); do DNS via Tor; and query other information from the
tor daemon.

txtorcon is the library to use if you want to write event-based
software in Python that uses the Tor network as a client or a service
(or **integrate Tor support for existing Twisted-using applications**,
or display information about a locally running tor). Twisted already
provides many robust protocol implementations, deployment, logging and
integration with GTK, Qt and other graphics frameworks -- so txtorcon
can be used for command-line or GUI applications or integrate with
long-lived daemons easily.

In fact, due to support for endpoints (adding the ``tor:`` and
``onion:`` plugins), many Twisted applications can now integrate with
Tor with **no code changes**. For example, you can use the existing
Twisted webserver via ``twistd`` to serve your ``~/public_html``
directory over an onion service:

.. code-block:: shell-session

   $ sudo apt-get install --install-suggests python-txtorcon
   $ twistd web --port "onion:80" --path ~/public_html

(You should ideally enable the `Tor project repositories
<https://www.torproject.org/docs/debian.html.en>`_ first).

txtorcon strives to provide sane and **safe** defaults. txtorcon is `a
Tor project
<https://www.torproject.org/projects/projects.html.en>`_. The
applications `Tahoe-LAFS <https://tahoe-lafs.org>`_ and `Crossbar.io
<https://crossbar.io>`_ have successfully integrated Tor support using
txtorcon.


.. _features:

Features Overview
-----------------

Currently, txtorcon is capable of:

- making arbitrary client connections to other services over Tor;
- configuring `twisted.web.client.Agent <https://twistedmatrix.com/documents/current/web/howto/client.html>`_ instances to do Web requests over Tor;
- doing both of the above over specific circuits;
- listening as an Onion service;
- maintaining up-to-date (live) state information about Tor: Circuits, Streams and Routers (relays);
- maintaining current (live) configuration information;
- maintaining representation of Tor's address mappings (with expiry);
- interrogating initial state of all three of the above;
- listening for and altering stream -> circuit mappings;
- building custom circuits;
- Circuit and Stream state listeners;
- listening for any Tor EVENT;
- launching and/or controlling a Tor instance (including Tor Browser Bundle);
- complete Twisted endpoint support (both "onion"/server side and
  client-side). This means you may be able to use *existing* Twisted
  software via Tor with **no code changes**. It also is the preferred
  way to connect (or listen) in Twisted.

Comments (positive or negative) appreciated. Even better if they come
with patches 😉


Shell-cast Overview
-------------------

A text-only screencast-type overview of some of txtorcon's features,
from asciinema.org:

.. role:: raw-html(raw)
   :format: html

:raw-html:`<script type="text/javascript" src="https://asciinema.org/a/eh2gxfz3rc1ztgapkcol47d6o.js" id="asciicast-eh2gxfz3rc1ztgapkcol47d6o" async></script>`


Example Code
------------

`download <examples/readme.py>`_
(also `python3 style <examples/readme3.py>`_)

.. literalinclude:: ../examples/readme.py


.. _known_users:

Known Users
-----------

- `magic-wormhole <https://github.com/warner/magic-wormhole>`_ "get things from one computer to another, safely"
- `Tahoe-LAFS <https://tahoe-lafs.org>`_ a Free and Open encrypted distributed storage system
- `Crossbar.io <https://crossbar.io>`_ a Free and Open distributed-systems (RPC and PubSub) protocol (called WAMP) router. Supports e2e-encrypted payloads.
- txtorcon received a brief mention `at 29C3 <http://media.ccc.de/browse/congress/2012/29c3-5306-en-the_tor_software_ecosystem_h264.html>`_ starting at 12:20 (or via `youtube <http://youtu.be/yG2-ci95h78?t=12m27s>`_).
- `carml <https://github.com/meejah/carml>`_ command-line utilities for Tor
- `foolscap <https://github.com/warner/foolscap/>`_ RPC system inspired by Twisted's built-in "Perspective Broker" package.
- `bwscanner <https://github.com/TheTorProject/bwscanner>`_ next-gen bandwidth scanner for Tor network
- `unmessage <https://github.com/AnemoneLabs/unmessage>`_ Privacy enhanced instant messenger
- `APAF <https://github.com/globaleaks/APAF>`_ anonymous Python application framework
- `OONI <https://ooni.torproject.org/>`_ the Open Observatory of Network Interference
- `exitaddr <https://github.com/arlolra/exitaddr>`_ scan Tor exit addresses
- `txtorhttpproxy <https://github.com/david415/txtorhttpproxy>`_ simple HTTP proxy in Twisted
- `bulb <https://github.com/arlolra/bulb>`_ Web-based Tor status monitor
- `onionvpn <https://github.com/david415/onionvpn>`_  "ipv6 to onion service virtual public network adapter"
- `torperf2 <https://github.com/gsathya/torperf2>`_ new Tor node network performance measurement service
- `torweb <https://github.com/coffeemakr/torweb>`_ web-based Tor controller/monitor
- `potator <https://github.com/mixxorz/potator>`_ "A Tor-based Decentralized Virtual Private Network Application"
