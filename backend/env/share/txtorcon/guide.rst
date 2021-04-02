.. _programming_guide:

Programming Guide
=================

.. contents::
    :depth: 2
    :local:
    :backlinks: none

.. _api_stability:

API Stability
-------------

In general, any method or class prefixed with an underscore (like
``_method`` or ``_ClassName``) is private, and the API may change at
any time. You SHOULD NOT use these. Any method in an interface class
(which all begin with ``I``, like ``IAnInterface``) are stable, public
APIs and will maintain backwards-compatibility between releases.

There is **one exception to this** at the moment: the hidden- / onion-
services APIs are NOT yet considered stable, and may still change
somewhat.

Any APIs that will go away will first be deprecated for at least one
major release before being removed.

There are also some attributes which *don't* have underscores but
really should; these will get "deprecated" via an ``@property``
decorator so your code will still work.


.. _guide_overview:

High Level Overview
-------------------

Interacting with Tor via txtorcon should involve *only* calling
methods of the :class:`.Tor` class.

You get an instance of :class:`.Tor` in one of two ways:

 - call :meth:`txtorcon.connect` or;
 - call :meth:`txtorcon.launch`

Once you've got a :class:`.Tor` instance you can use it to gain access to
(or create) instances of the other interesting classes; see "A Tor
Instance" below for various use-cases.

Note that for historical reasons (namely: :class:`.Tor` is a
relatively new class) there are many other functions and classes
exported from txtorcon but you *shouldn't* need to instantiate these
directly. If something is missing from this top-level class, please
get in touch (file a bug, chat on IRC, etc) because it's probably a
missing feature.


.. _guide_tor_instance:

A Tor Instance
--------------

You will need a connection to a Tor instance for txtorcon to
control. This can be either an already-running Tor that you're
authorized to connect to, or a Tor instance that has been freshly
launched by txtorcon.

We abstract "a Tor instance" behind the :class:`.Tor` class,
which provides a very high-level API for all the other things you
might want to do:

 - make client-type connections over tor (see ":ref:`guide_client_use`");
 - change its configuration (see ":ref:`guide_configuration`");
 - monitor its state (see ":ref:`guide_state`");
 - offer hidden-/onion- services via Tor (see ":ref:`guide_onions`");
 - create and use custom circuits (see ":ref:`guide_custom_circuits`");
 - issue low-level commands (see ":ref:`protocol`")

The actual control-protocol connection to tor is abstracted behind
:class:`.TorControlProtocol`. This can usually be ignored by
most users, but can be useful to issue protocol commands directly,
listen to raw events, etc.

In general, txtorcon tries to never look at Tor's version and instead
queries required information directly via the control-protocol (there
is only one exception to this). So the names of configuration values
and events may change (or, more typically, expand) depending on what
version of Tor you're connected to.


Connecting to a Running Tor
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tor can listen for control connections on TCP ports or UNIX
sockets. See ":ref:`configure_tor`" for information on how to
configure Tor to work with txtorcon. By default, "COOKIE"
authentication is used; only if that is not available do we try
password authentication.

To connect, use :meth:`txtorcon.connect` which returns a Deferred that
will fire with a :class:`.Tor` instance. If you need access to the
:class:`.TorControlProtocol` instance, it's available via the
``.protocol`` property (there is always exactly one of these per
:class:`.Tor` instance). Similarly, the current configuration is
available via ``.get_config`` (which returns a Deferred firing a
:class:`.TorConfig`). You can change the configuration by updating
attributes on this class but it won't take effect until you call
:meth:`.TorConfig.save`.


Launching a New Tor
~~~~~~~~~~~~~~~~~~~

It's also possible to launch your own Tor instance. txtorcon keeps a
"global" tor available for use by e.g. the ``.global_tor`` endpoint
factory functions (like
:func:`.TCPHiddenServiceEndpoint.global_tor`). You can access
it via :func:`.get_global_tor_instance`. There is exactly zero
or one of these *per Python process* that uses ``txtorcon``.

To explicitly launch your own Tor instance, use
:meth:`.launch`. You can pass a couple of minimal options
(``data_directory`` being recommended). If you need to set other Tor
options, use ``.config`` to retrieve the :class:`.TorConfig`
instance associated with this tor and change configuration afterwards.

Setting ``data_directory`` gives your Tor instance a place to cache
its state information which includes the current "consensus"
document. If you don't set it, txtorcon creates a temporary directly
(which is deleted when this Tor instance exits). Startup time is
drammatically improved if Tor already has a recent consensus, so when
integrating with Tor by launching your own client it's highly
recommended to specify a ``data_directory`` somewhere sensible
(e.g. ``~/.config/your_program_name/`` is a popular choice on
Linux). See `the Tor manual`_ under the
``DataDirectory`` option for more information.

Tor itself will create a missing ``data_directory`` with the correct
permissions and Tor will also ``chdir`` into its ``DataDirectory``
when running. For these reasons, txtorcon doesn't try to create the
``data_directory`` nor do any ``chdir``-ing, and neither should you.


.. _guide_style:

A Note On Style
---------------

Most of txtorcon tends towards "attribute-style access".  The guiding
principle is that "mere data" that is immediately available will be an
attribute, whereas things that "take work" or are async (and thus
return ``Deferred`` s) will be functions. For example,
:meth:`.Router.get_location` is a method because it
potentially has to ask Tor for the country, whereas
:attr:`.Router.hex_id` is a plain attribute because it's
always available.


.. _guide_configuration:

Tracking and Changing Tor's Configuration
-----------------------------------------

Instances of the :class:`.TorConfig` class represent the
current, live state of a running Tor. There is a bit of
attribute-magic to make it possible to simply get and set things
easily:

.. sourcecode:: python

    tor = launch(..)
    print("SOCKS ports: {}".format(tor.config.SOCKSPort))
    tor.config.ControlPort.append(4321)
    tor.config.save()

**Only when** ``.save()`` is called are any ``SETCONF`` commands
issued -- and then, all configuration values are sent in a single
command. All ``TorConfig`` instances subscribe to configuration
updates from Tor, so **"live state" includes actions by any other
controllers that may be connected**.

For some configuration items, the order they're sent to Tor
matters. Sometimes, if you change one config item, you have to set a
series of related items. TorConfig handles these cases for you -- you
just manipulate the configuration, and wait for ``.save()`` 's
``Deferred`` to fire and the running Tor's configuration is updated.

Note there is a tiny window during which the state may appear slightly
inconsistent if you have multiple ``TorConfig`` instances: after Tor
has acknowledged a ``SETCONF`` command, but before a separate
``TorConfig`` instance has gotten all the ``CONF_CHANGED`` events
(because they're hung up in the networking stack for some
reason). This shouldn't concern most users. (I'm not even 100% sure
this is possible; it may be that Tor doesn't send the OK until after
all the CONF_CHANGED events). In normal use, there should only be a
single ``TorConfig`` instance for every ``Tor`` instance so this
shouldn't affect you unless you've created your own ``TorConfig``.

Since :class:`.TorConfig` conforms to the Iterator protocol,
you can easily find all the config-options that Tor supports:

.. sourcecode:: python

    tor = launch(..)
    for config_key in tor.config:
        print("{} has value: {}".format(config_key, getattr(tor.config.config_key)))

.. fixme::  why doesn't dir() work; fix it, or mention it here


These come from interrogating Tor using ``GETINFO config/names`` and
so represent the configuration options of the current connected Tor
process. If the value "isn't set" (i.e. is the default), the value
from Tor will be ``.DEFAULT_VALUE``.

When you set values into ``TorConfig``, they are parsed according to
control-spec for the different types given to the values, via
information from ``GETINFO config/names``. So, for example, setting
``.SOCKSPort`` to a ``"quux"`` won't work. Of course, it would also
fail the whole ``SETCONF`` command if txtorcon happens to allow some
values that Tor doesn't. Unfortunately, **for any item that's a
list**, Tor doesn't tell us anything about each element so they're all
strings. This means we can't pre-validate them and so some things may
not fail until you call ``.save()``.


.. _guide_state:

Monitor and Change Tor's State
------------------------------

Instances of :class:`.TorState` prepresent a live, interactive
version of all the relays/routers (:class:`.Router`
instances), all circuits (:class:`.Circuit` instances) and
streams (:class:`.Stream` instances) active in the underlying
Tor instance.

As the ``TorState`` instance has subscribed to various events from
Tor, the "live" state represents an "as up-to-date as possible"
view. This includes all other controlers, Tor Browser, etcetera that
might be interacting with your Tor client.

A ``Tor`` instance doesn't have a ``TorState`` instance by default (it
can take a few hundred milliseconds to set up) and so one is created
via the asynchronous method :meth:`.Tor.get_state`.

.. note::

    If you need to be **absolutely sure** there's nothing stuck in
    networking buffers and that your instance is "definitely
    up-to-date" you can issue a do-nothing command to Tor via
    :meth:`.TorControlProtocol.queue_command` (e.g. ``yield
    queue_command("GETINFO version")``). Most users shouldn't have to
    worry about this edge-case. In any case, there could be a new
    update that Tor decides to issue at any moment.

You can modify the state of Tor in a few simple ways. For example, you
can call :meth:`.Stream.close` or
:meth:`.Circuit.close` to cause a stream or circuit to be
closed. You can wait for a circuit to become usable with
:meth:`.Circuit.when_built`.

For a lot of the read-only state, you can simply access interesting
attributes. The relays through which a circuit traverses are in
``Circuit.path`` (a list of :class:`.Router` instances),
``Circuit.streams`` contains a list of :class:`.Stream`
instances, ``.state`` and ``.purpose`` are strings. ``.time_created``
returns a `datetime
<https://docs.python.org/2/library/datetime.html>`_ instance. There
are also some convenience functions like :meth:`.Circuit.age`.

For sending streams over a particular circuit,
:meth:`.Circuit.stream_via` returns an
`IStreamClientEndpoint`_ implementation that will cause a subsequent
``.connect()`` on it to go via the given circuit in Tor. A similar
method (:meth:`.Circuit.web_agent`) exists for Web requests.

Listening for certain events to happen can be done by implementing the
interfaces :class:`.interface.IStreamListener` and
:class:`.interface.ICircuitListener`. You can request
notifications on a Tor-wide basis with
:meth:`.TorState.add_circuit_listener` or
:meth:`.TorState.add_stream_listener`. If you are just
interested in a single circuit, you can call
:meth:`.Circuit.listen` directly on a ``Circuit`` instance.

The Tor relays are abstracted with :class:`.Router`
instances. Again, these have read-only attributes for interesting
information, e.g.: ``id_hex``, ``ip``, ``flags`` (a list of strings),
``bandwidth``, ``policy``, etc. Note that all information in these
objects is from "microdescriptors". If you're doing a long-running
iteration over relays, it may be important to remember that the
collection of routers can change every hour (when a new "consensus"
from the Directory Authorities is published) which may change the
underlying collection (e.g. :attr:`.TorState.routers_by_hash`)
over which you're iterating.

Here's a simple sketch that traverses all circuits printing their
router IDs, and closing each stream and circuit afterwards:

.. literalinclude:: ../examples/close_all_circuits.py


.. _guide_client_use:

Making Connections Over Tor
---------------------------

SOCKS5
~~~~~~

Tor exposes a SOCKS5 interface to make client-type connections over
the network. There are also a couple of `custom extensions
<https://gitweb.torproject.org/torspec.git/tree/socks-extensions.txt>`_
Tor provides to do DNS resolution over a Tor circuit (txtorcon
supports these, too).

All client-side interactions are via instances that implement
`IStreamClientEndpoint`_. There are several factory functions used to
create suitable instances.

The recommended API is to acquire a :class:`.Tor` instance
(see ":ref:`guide_tor_instance`") and then call
:meth:`.Tor.create_client_endpoint`. To do DNS lookups (or
reverse lookups) via a Tor circuit, use
:meth:`.Tor.dns_resolve` and
:meth:`.Tor.dns_resolve_ptr`.

A common use-case is to download a Web resource; you can do so via
Twisted's built-in ``twisted.web.client`` package, or using the
friendlier `treq`_ library. In both cases, you need a
`twisted.web.client.Agent
<https://twistedmatrix.com/documents/current/api/twisted.web.client.Agent.html>`_
instance which you can acquire with :meth:`.Tor.web_agent` or
:meth:`.Circuit.web_agent`. The latter is used to make the
request over a specific circuit. Usually, txtorcon will simply use one
of the available SOCKS ports configured in the Tor it is connected to
-- if you care which one, you can specify it as the optional
``_socks_endpoint=`` argument (this starts with an underscore on
purpose as it's not recommended for "public" use and its semantics
might change in the future).

.. note::

   Tor supports SOCKS over Unix sockets. So does txtorcon. To take
   advantage of this, simply pass a valid ``SocksPort`` value for unix
   sockets (e.g. ``unix:/tmp/foo/socks``) as the ``_socks_endpoint``
   argument to either ``web_agent()`` call. If this doesn't already
   exist in the underlying Tor, it will be added. Tor has particular
   requirements for the directory in which the socket file is
   (``0700``). We don't have a way (yet?) to auto-discover if the Tor
   we're connected to can support Unix sockets so the default is to
   use TCP.

You can also use Twisted's `clientFromString`_ API as txtorcon
registers a ``tor:`` plugin. This also implies that any Twisted-using
program that supports configuring endpoint strings gets Tor support
"for free". For example, passing a string like
``tor:timaq4ygg2iegci7.onion:80`` to `clientFromString`_ will return
an endpoint that will connect to txtorcon's onion-service
website. Note that these endpoints will use the "global to txtorcon"
Tor instance (available from :meth:`.get_global_tor`). Thus,
if you want to control *which* tor instance your circuit goes over,
this is not a suitable API.

There are also lower-level APIs to create
:class:`.TorClientEndpoint` instances directly if you have a
:class:`.TorConfig` instance. These very APIs are used by the
``Tor`` object mentioned above. If you have a use-case that *requires*
using this API, I'd be curious to learn why the :class:`.Tor`
methods are un-suitable (as those are the suggested API).

You should expect these APIs to raise SOCKS5 errors, which can all be
handled by catching the :class:`.socks.SocksError` class. If
you need to work with each specific error (corresponding to the
`RFC-specified SOCKS5 replies`_), see the ":ref:`socks`" for a list of
them.

.. _guide_onions:

.. _server_use:

Onion (Hidden) Services
-----------------------

An "Onion Service" (also called a "Hidden Service") refers to a
feature of Tor allowing servers (e.g. a Web site) to be availble via
Tor. These bring additional security properties such as:

 * hiding the server's network location;
 * providing end-to-end encryption;
 * self-certifying domain-names;
 * NAT penetration (connections to Tor network are client-like);
 * or offering authentication.

For details of how this works, please read `Tor's documentation on
Hidden Services
<https://www.torproject.org/docs/hidden-services.html.en>`_.

For more background, the `RiseUp Onion service best-practices guide
<https://riseup.net/en/security/network-security/tor/onionservices-best-practices>`_
is a good read as well.

In the newest Tor versions, Onion services have been upgraded
("`Proposition 279
<https://gitweb.torproject.org/torspec.git/plain/proposals/279-naming-layer-api.txt>`_")
and these are known as "version 3" services. The prior / legacy is
"version 2". In txtorcon, the default version is **usually** 3 but in
some older APIs the default has to remain "2" if unspecified (for
backwards-compatibility). You should thus usually pass ``version=3``
(and if you expect to connect to an older Tor release, pass
``version=2``).

.. note::

   In some places there will be "Hidden" in a classname; these are
   typically for backwards-compatilibity reasons. "Onion service" is
   the preferred name.

From an API perspective, here are the parts we care about:

- each service has a secret, private key (with a corresponding public
  part);
   - these keys can be on disk (in the "hidden service directory");
   - or, they can be "ephemeral" (only in memory);
- the "host name" is a hash of the public-key (e.g. ``timaq4ygg2iegci7.onion``);
- a "Descriptor" (which tells clients how to connect) must be
  published (to a "Hidden Service Directory", or HSDir);
- a service has a list of port-mappings (public -> local):
   - e.g. ``"80 127.0.0.1:5432"`` says you can contact the service
     publically on port 80, which Tor will redirect to a daemon
     running locally on port ``5432``;
   - note that "Descriptors" only show the public port
- services can be "authenticated", which means they have a list of
  client names for which Tor creates associated keys (``.auth_token``).
- Tor has two flavours of service authentication: ``basic`` and
  ``stealth`` -- there's no API-level difference, but the
  ``.hostname`` is unique for each client in the ``stealth`` case.

To summarize the above in a table format, here are the possible types
of Onion Service interfaces classes you may interact with.

+----------------------------------+-------------------------------------------+--------------------------------------------+
|                                  | Keys on disk                              | Keys in memory                             |
+==================================+===========================================+============================================+
|      **no authentication**       | :obj:`txtorcon.IFilesystemOnionService`   | :obj:`txtorcon.IOnionService`              |
+----------------------------------+-------------------------------------------+--------------------------------------------+
| **basic/stealth authentication** | :obj:`txtorcon.IAuthenticatedOnionClients`| :obj:`txtorcon.IAuthenticatedOnionClients` |
+----------------------------------+-------------------------------------------+--------------------------------------------+

:obj:`txtorcon.IFilesystemOnionService` is a subclass of
:obj:`txtorcon.IOnionService` and the concrete objects will
be different for on-disk versus in-memory keys; depend on the
methods in the interfaces (only).

Note that it's **up to you to save the private keys** of ephemeral
services if you want to re-launch them later; the "ephemeral" refers
to the fact that Tor doesn't persist the private keys -- when Tor
shuts down, they're gone and there will never be a service at the same
URI again (unless you saved the key).


Onion Services Endpoints API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

No matter which kind of service you need, you interact via Twisted's
`IStreamServerEndpoint`_ interface. There are various txtorcon methods
(see ":ref:`create_onion`") which return some instance implementing that
interface. These instances will also implement
:obj:`txtorcon.IProgressProvider` -- which is a hook to register
listeners which get updates about Tor's launching progress (if we
started a new Tor) and Descriptor uploading.

Fundamentally, "authenticated" services are different from
non-authenticated services because they have a list of
clients. Services on-disk are "slightly" different because the user
may need to know the "hidden service dir" that contains the private
keys. However, there is a single endpoint which takes enough options
to produce any kind of onion service. The service instance you
retrieve after the ``.listen()`` call will, however, be different and
implement one of the interfaces in the table above. Those are:

 - :obj:`txtorcon.IOnionService`
 - :obj:`txtorcon.IFilesystemOnionService` (also includes all of ``IOnionService``)
 - :obj:`txtorcon.IAuthenticatedOnionClients` (for authenticated services)

The ``.listen()`` method of the endpoint will return an instance
implementing `IListeningPort`_. This will have a ``.onion_service``
property that gives you an instance implementing one of the above
interfaces.

:obj:`txtorcon.IOnionService` and its subclass
:obj:`txtorcon.IFilesystemOnionService` correspond to a
non-authenticated services, while
:obj:`txtorcon.IAuthenticatedOnionClients` is authenticated. The latter
manages a collection of instances by (arbitrary) client names, where
each of these instances implements
:obj:`txtorcon.IOnionClient`. Note that the ``.auth_token`` member
is secret, private data which you need to give to **one** client; this
information goes in the client's Tor configuration as ``HidServAuth
onion-address auth-cookie [service-name]``. See `the Tor manual`_ for
more information.


.. _create_onion:

Creating Onion Endpoints
~~~~~~~~~~~~~~~~~~~~~~~~

The easiest-to-use API are methods of :class:`.Tor`, which
allow you to create `IStreamServerEndpoint`_ instances for the various
Onion Service types. For all service types there is a single endpoint
that you create: :class:`.TCPHiddenServiceEndpoint`. Thus, you
**are advised to use a factory-method to create the instance**

It's also possible to use Twisted's ``serverFromString`` API with the
``onion:`` prefix. (Thus, any program supporting endpoint strings for
configuration can use Tor Onion Services with *no code changes*).

Each of the four main classes of onion service has a corresponding
factory method (while these get nearly to Java lengths, these are at
least explicit):

 - :meth:`.Tor.create_onion_endpoint`: ephemeral service
 - :meth:`.Tor.create_authenticated_onion_endpoint`: ephemeral service with authentication
 - :meth:`.Tor.create_filesystem_onion_endpoint`: on-disk service
 - :meth:`.Tor.create_authenticated_filesystem_onion_endpoint`: on-disk service with authentication

Factors to consider when deciding whether to use "authenticated"
service or not:

 - if you want anyone with e.g. the URL http://timaq4ygg2iegci7.onion
   to be able to put it in `Tor Browser Bundle
   <https://www.torproject.org/download/download.html.en>`_ and see a
   Web site, you **do not want** authentication;
 - if you want only people with the URL *and* a secret authentication
   token to see the Web site, you want **basic** authentication (these
   support many more clients than stealth auth);
 - if you don't even want anyone to be able to decrypt the descriptor
   without a unique URL *and* a secret authentication token, you want
   **stealth** authentication (a lot less scalable; for only "a few"
   clients -- less than 16 in latest Tor).


Non-Authenticated Services
~~~~~~~~~~~~~~~~~~~~~~~~~~

You can create non-authenticated with
:meth:`.Tor.create_onion_service` (for an ephemeral service)
or :meth:`.Tor.create_filesystem_onion_service` (for an
on-disk service).

If you don't want to manage launching or connecting to Tor yourself
(and thus a :class:`.Tor` instance), you can use one of the
three factory-functions in :class:`.TCPHiddenServiceEndpoint`,
which all return a new endpoint instance:

 - :meth:`.TCPHiddenServiceEndpoint.global_tor`: uses a Tor
   instance launched at most once in this Python process (the
   underlying :class:`.Tor` instance for this is available via
   :func:`.get_global_tor()` if you need to make manual
   configuration adjustments);

 - :meth:`.TCPHiddenServiceEndpoint.system_tor`: connects to
   the control-protocol endpoint you provide (a good choice on Debian
   would be ``UNIXClientEndpoint('/var/run/tor/control')``);

 - :meth:`.TCPHiddenServiceEndpoint.private_tor`: causes a
   fresh, private instance of Tor to be launched for this service
   alone. This uses a tempdir (honoring ``$TMP``) which is deleted
   upon reactor shutdown or loss of the control connection.

Note that nothing actually "happens" until you call ``.listen()`` on
the ``IStreamServerEndpoint`` at which point Tor will possibly be
launched, the Onion Service created, and the descriptor published.


Authenticated Services
~~~~~~~~~~~~~~~~~~~~~~

Authenticated services take an instance of :class:`.AuthBasic`
or :class:`.AuthStealth`. You may use the factory methods on
:class:`.Tor`:
:meth:`.Tor.create_authenticated_onion_service` (for an
ephemeral service) or
:meth:`.Tor.create_authenticated_filesystem_onion_service`
(for an on-disk service).

You may also use one of the three ``@classmethod``-s on
:class:`.TCPHiddenServiceEndpoint` (and passing an `auth=`
kwarg):

 - :meth:`.TCPHiddenServiceEndpoint.global_tor`
 - :meth:`.TCPHiddenServiceEndpoint.system_tor`
 - :meth:`.TCPHiddenServiceEndpoint.private_tor`


Onion Service Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you just want to "look at" the configuration of existing onion
services, they are avaialble via :class:`.TorConfig` and the
``.HiddenServices`` or ``.EphemeralHiddenServices`` attributes.

These presents a "flattened" version of any authenticated services, so
that each element in the list of ``.HiddenServices`` is itself at
least a :obj:`txtorcon.IOnionService` (it may also implement other
interfaces, but every one will implement ``IOnionService``).

You can still set any settable attributes on these objects, and Tor's
configuration for them will be updated when you call
:meth:`.TorConfig.save` with an **important exception**:
"ephemeral" services cannot be updated after they're created.

Note that it's possible for other controllers to create ephemeral
services that Tor doesn't allow your controller to enumerate.


.. _guide_custom_circuits:

Custom Circuits
---------------

Tor provides a way to let controllers like txtorcon decide which
streams go on which circuits. Since your Tor client will then be
acting differently from a "normal" Tor client, it **may become easier
to de-anonymize you**.

High Level
~~~~~~~~~~

With that in mind, you may still decide to attach streams to
circuits. Most often, this means you simply want to make a client
connection over a particluar circuit. The recommended API uses
:meth:`.Circuit.stream_via` for arbitrary protocols or
:meth:`.Circuit.web_agent` as a convenience for Web
connections. The latter can be used via `Twisted's Web client
<https://twistedmatrix.com/documents/current/web/howto/client.html>`_
or via `treq`_ (a "requests"-like library for Twisted).

See the following examples:

 - :ref:`web_client.py`
 - :ref:`web_client_treq.py`
 - :ref:`web_client_custom_circuit.py`

Note that these APIs mimic :meth:`.Tor.stream_via` and
:meth:`.Tor.web_agent` except they use a particular Circuit.


Low Level
~~~~~~~~~

Under the hood of these calls, txtorcon provides a low-level interface
directly over top of Tor's circuit-attachment API.

This works by:

 - setting ``__LeaveStreamsUnattached 1`` in the Tor's configuration
 - listening for ``STREAM`` events
 - telling Tor (via ``ATTACHSTREAM``) what circuit to put each new
   stream on
 - (we can also choose to tell Tor "attach this one however you
   normally would")

This is an asynchronous API (i.e. Tor isn't "asking us" for each
stream) so arbitrary work can be done on a per-stream basis before
telling Tor which circuit to use. There are two limitations though:

 - Tor doesn't play nicely with multiple controllers playing the role
   of attaching circuits. Generally, there's not a good way to know if
   there's another controller trying to attach streams, but basically the
   first one to answer "wins".
 - Tor doesn't currently allow controllers to attach circuits destined
   for onion-services (even if the circuit is actually suitable and
   goes to the correct Introduction Point).

In order to do custom stream -> circuit mapping, you call
:meth:`.TorState.set_attacher` with an object implementing
:class:`.interface.IStreamAttacher`. Then every time a new
stream is detected, txtorcon will call
:meth:`.interface.IStreamAttacher.attach_stream` with the
:class:`.Stream` instance and a list of all available
circuits. You make an appropriate return.

There can be either no attacher at all or a single attacher
object. You can "un-set" an attacher by calling ``set_attacher(None)``
(in which case ``__LeaveStreamsUnattached`` will be set back to 0).
If you really do need multiple attachers, you can use the utility
class :class:`.attacher.PriorityAttacher` which acts as the
"top level" one (so you add your multiple attachers to it).

Be aware that txtorcon internally uses this API itself if you've
*ever* called the "high level" API
(:meth:`.Circuit.stream_via` or
:meth:`.Circuit.web_agent`) and so it is an **error** to set a
new attacher if there is already an existing attacher.


.. _guide_building_circuits:

Building Your Own Circuits
--------------------------

To re-iterate the warning above, making your own circuits differently
from how Tor normally does **runs a high risk of de-anonymizing
you**. That said, you can build custom circuits using txtorcon.


Building a Single Circuit
~~~~~~~~~~~~~~~~~~~~~~~~~

If your use-case needs just a single circuit, it is probably easiest
to call :meth:`.TorState.build_circuit`. This methods takes a
list of :class:`.Router` instances, which you can get from the
:class:`.TorState` instance by using one of the attributes:

 - ``.all_routers``
 - ``.routers``
 - ``.routers_by_name`` or
 - ``.routers_by_hash``

The last three are all dicts. For relays that have the ``Guard`` flag,
you can access the dicts ``.guards`` (for **all** of them) or
``.entry_guards`` (for just the entry guards configured on this Tor
client).

If you don't actually care which relays are used, but simply want a
fresh circuit, you can call :meth:`.TorState.build_circuit`
without any arguments at all which asks Tor to build a new circuit in
the way it normally would (i.e. respecting your guard nodes etc).

There is also :func:`.build_timeout_circuit` as a convenience method
if you wish the attempt to time out after a while.


.. _circuit_builder:

Building Many Circuits
~~~~~~~~~~~~~~~~~~~~~~

.. caution::

   This API doesn't exist yet; this is documenting what **may** become
   a new API in a future version of txtorcon. Please get in touch if
   you want this now.

If you would like to build many circuits, you'll want an instance that
implements :obj:`txtorcon.ICircuitBuilder` (which is usually simply
an instance of :class:`.CircuitBuilder`). Instances of this
class can be created by calling one of the factory functions like
:func:`.circuit_builder_fixed_exit`.

XXX what about a "config object" idea, e.g. could have keys:

 - ``guard_selection``: one of ``entry_only`` (use one of the current
   entry guards) or ``random_guard`` (use any relay with the Guard
   flag, selected by XXX).
 - ``middle_selection``: one of ``uniform`` (selected randomly from
   all relays), ``weighted`` (selected randomly, but weighted by
   consensus weight -- basically same way as Tor would select).


.. _istreamclientendpoint: http://twistedmatrix.com/documents/current/api/twisted.internet.interfaces.IStreamClientEndpoint.html
.. _istreamserverendpoint: http://twistedmatrix.com/documents/current/api/twisted.internet.interfaces.IStreamServerEndpoint.html
.. _clientfromstring: http://twistedmatrix.com/documents/current/api/twisted.internet.endpoints.html#clientFromString
.. _serverfromstring: http://twistedmatrix.com/documents/current/api/twisted.internet.endpoints.html#serverFromString
.. _ilisteningport: http://twistedmatrix.com/documents/current/api/twisted.internet.interfaces.IListeningPort.html
.. _treq: https://treq.readthedocs.io/en/latest/
.. _`rfc-specified socks5 replies`: https://tools.ietf.org/html/rfc1928#section-6
.. _`the Tor manual`: https://www.torproject.org/docs/tor-manual.html.en
