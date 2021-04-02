.. _interop_asyncio:

Using Asyncio Libraries with txtorcon
=====================================

It is possible to use Twisted's `asyncioreactor
<https://twistedmatrix.com/documents/current/api/twisted.internet.asyncioreactor.html>`_
in order to use Twisted together with asyncio libraries. This comes
with a couple caveats:

* You need to install Twisted
* Twisted "owns" the event-loop (i.e. you call :func:`reactor.run`);
* You need to convert Futures/co-routines to Deferred sometimes
  (Twisted provides the required machinery)

Here is an example using the `aiohttp
<https://aiohttp.readthedocs.io/en/stable/>`_ library as a Web server
behind an Onion service that txtorcon has set up (in a newly-launched
Tor process):

**wanted**: I can't get this example to work properly with a Unix
socket.

.. _web_onion_service_aiohttp.py:

``web_onion_service_aiohttp.py``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:download:`Download the example <../examples/web_onion_service_aiohttp.py>`.

.. literalinclude:: ../examples/web_onion_service_aiohttp.py
