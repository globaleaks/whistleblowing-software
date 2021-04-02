.. _onion_api:

Onion APIs
==========

See the :ref:`programming_guide` for "prose" documentation of these
(and other) APIs.

For non-authenticated services:

IOnionService
-------------
.. autointerface:: txtorcon.IOnionService

IFilesystemOnionService
-----------------------
.. autointerface:: txtorcon.IFilesystemOnionService



Both kinds of authenticated service (ephemeral or disk) implement
these interfaces:

IAuthenticatedOnionClients
--------------------------
.. autointerface:: txtorcon.IAuthenticatedOnionClients

IOnionClient
------------
.. autointerface:: txtorcon.IOnionClient


Concrete classes implementing specific variations of Onion
services. First, ephemeral services (private keys do not live on
disk). See :ref:`server_use` for an overview of the variations.

EphemeralOnionService
---------------------
.. autoclass:: txtorcon.EphemeralOnionService

EphemeralAuthenticatedOnionService
----------------------------------
.. autoclass:: txtorcon.EphemeralAuthenticatedOnionService

EphemeralAuthenticatedOnionServiceClient
----------------------------------------
.. autoclass:: txtorcon.EphemeralAuthenticatedOnionServiceClient


Onion services which store their secret keys on disk:

FilesystemOnionService
----------------------
.. autoclass:: txtorcon.FilesystemOnionService

FilesystemAuthenticatedOnionService
-----------------------------------
.. autoclass:: txtorcon.FilesystemAuthenticatedOnionService

FilesystemAuthenticatedOnionServiceClient
-----------------------------------------
.. autoclass:: txtorcon.FilesystemAuthenticatedOnionServiceClient


Some utility-style classes:

AuthBasic
---------
.. autoclass:: txtorcon.AuthBasic

AuthStealth
-----------
.. autoclass:: txtorcon.AuthStealth

