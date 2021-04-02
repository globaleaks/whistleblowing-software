.. _socks:

:mod:`txtorcon.socks` Module
============================

SOCKS5 Errors
-------------

SocksError
~~~~~~~~~~
.. autoclass:: txtorcon.socks.SocksError


GeneralServerFailureError
~~~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: txtorcon.socks.GeneralServerFailureError


ConnectionNotAllowedError
~~~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: txtorcon.socks.ConnectionNotAllowedError


NetworkUnreachableError
~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: txtorcon.socks.NetworkUnreachableError


HostUnreachableError
~~~~~~~~~~~~~~~~~~~~
.. autoclass:: txtorcon.socks.HostUnreachableError


ConnectionRefusedError
~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: txtorcon.socks.ConnectionRefusedError


TtlExpiredError
~~~~~~~~~~~~~~~
.. autoclass:: txtorcon.socks.TtlExpiredError


CommandNotSupportedError
~~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: txtorcon.socks.CommandNotSupportedError


AddressTypeNotSupportedError
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: txtorcon.socks.AddressTypeNotSupportedError


.. note::
    The following sections present low-level APIs. If you are able
    to work with :class:`txtorcon.Tor`'s corresponding high-level
    APIs, you should do so.


resolve
-------
.. autofunction:: txtorcon.socks.resolve


resolve_ptr
-----------
.. autofunction:: txtorcon.socks.resolve_ptr


TorSocksEndpoint
----------------
.. autoclass:: txtorcon.socks.TorSocksEndpoint
