.. _examples:

Examples
========

The examples are grouped by functionality and serve as mini-HOWTOs --
if you have a use-case that is missing, it may be useful to add an
example, so please file a bug.

All files are in the :file:`examples/` sub-directory and are ready to
run, usually with defaults designed to work with Tor Browser Bundle
(``localhost:9151``).

The examples use `default_control_port()` to determine how to connect
which you can override with an environment variable:
`TX_CONTROL_PORT`. So e.g. `export TX_CONTROL_PORT=9050` to run the
examples again a system-wide Tor daemon.


.. contents::
   :depth: 2
   :local:
   :backlinks: none


Web: clients
------------


.. _web_client.py:

``web_client.py``
~~~~~~~~~~~~~~~~~

:download:`Download the example <../examples/web_client.py>`.

Uses `twisted.web.client
<http://twistedmatrix.com/documents/current/web/howto/client.html>`_
to download a Web page using a ``twisted.web.client.Agent``, via any
circuit Tor chooses.

.. literalinclude:: ../examples/web_client.py



.. _web_client_treq.py:

``web_client_treq.py``
~~~~~~~~~~~~~~~~~~~~~~

:download:`Download the example <../examples/web_client_treq.py>`.

Uses `treq <https://treq.readthedocs.io/en/latest/>`_ to download a
Web page via Tor.

.. literalinclude:: ../examples/web_client_treq.py



.. _web_client_custom_circuit.py:

``web_client_custom_circuit.py``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:download:`Download the example <../examples/web_client_custom_circuit.py>`.

Builds a custom circuit, and then uses `twisted.web.client
<http://twistedmatrix.com/documents/current/web/howto/client.html>`_
to download a Web page using the circuit created.

.. literalinclude:: ../examples/web_client_custom_circuit.py


Starting Tor
------------

.. _launch_tor.py:

:file:`launch_tor.py`
~~~~~~~~~~~~~~~~~~~~~

:download:`Download the example <../examples/launch_tor.py>`.  Launch
a new Tor instance. This takes care of setting Tor's notion ownership
so that when the control connection goes away the running Tor exits.

.. literalinclude:: ../examples/launch_tor.py


.. _launch_tor_endpoint.py:

:file:`launch_tor_endpoint.py`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:download:`Download the example
<../examples/launch_tor_endpoint.py>`. Using the
:class:`txtorcon.TCP4HiddenServiceEndpoint` class to start up a Tor
with a hidden service pointed to an
:api:`twisted.internet.interfaces.IStreamServerEndpoint
<IStreamServerEndpoint>`.

.. literalinclude:: ../examples/launch_tor_endpoint.py


Circuits and Streams
--------------------

.. _disallow_streams_by_port.py:

:file:`disallow_streams_by_port.py`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:download:`Download the example <../examples/disallow_streams_by_port.py>`.
An example using :class:`~txtorcon.torstate.IStreamAttacher` which is
very simple and does just what it sounds like: never attaches Streams
exiting to a port in the "disallowed" list (it also explicitly closes
them). Note that **Tor already has this feature**; this is just to
illustrate how to use IStreamAttacher and that you may close streams.

XXX keep this one?

.. literalinclude:: ../examples/disallow_streams_by_port.py



.. _stream_circuit_logger.py:

:file:`stream_circuit_logger.py`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:download:`Download the example <../examples/stream_circuit_logger.py>`.
For listening to changes in the Circuit and State objects, this
example is the easiest to understand as it just prints out (some of)
the events that happen. Run this, then visit some Web sites via Tor to
see what's going on.

.. literalinclude:: ../examples/stream_circuit_logger.py


Events
------


.. _monitor.py:

:file:`monitor.py`
~~~~~~~~~~~~~~~~~~

:download:`Download the example <../examples/monitor.py>`.

Use a plain :class:`txtorcon.TorControlProtocol` instance to listen
for some simple events -- in this case marginally useful, as it
listens for logging at level ``INFO``, ``NOTICE``, ``WARN`` and ``ERR``.

.. literalinclude:: ../examples/monitor.py



Miscellaneous
-------------


.. _stem_relay_descriptor.py:

:file:`stem_relay_descriptor.py`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:download:`Download the example <../examples/stem_relay_descriptor.py>`.

Get information about a relay descriptor with the help of `Stem's Relay Descriptor class
<https://stem.torproject.org/api/descriptor/server_descriptor.html#stem.descriptor.server_descriptor.RelayDescriptor>`_.
We need to specify the nickname or the fingerprint to get back
the details.

.. literalinclude:: ../examples/stem_relay_descriptor.py




.. _txtorcon.tac:

:file:`txtorcon.tac`
~~~~~~~~~~~~~~~~~~~~

:download:`Download the example <../examples/txtorcon.tac>`

Create your own twisted `Service` for deploying using ``twistd``.

.. literalinclude:: ../examples/txtorcon.tac

