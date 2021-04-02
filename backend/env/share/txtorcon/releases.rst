.. _releases:

Releases
========

There isn't a "release schedule" in any sense. If there is something
in master your project depends upon, let me know and I'll do a
release.

txtorcon follows `calendar versioning <http://calver.org/>`_ with the
major version being the 2-digit year. The second digit will be
"non-trivial" releases and the third will be for bugfix releases. So
the second release in 2019 would be "19.2.0" and a bug-fix release of
that will be "19.2.1".

See also :ref:`api_stability`.


unreleased
----------

`git master <https://github.com/meejah/txtorcon>`_ *will likely become v19.0.0*

v18.3.0
-------

 * `txtorcon-18.3.0.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-18.3.0.tar.gz>`_ (`PyPI <https://pypi.python.org/pypi/txtorcon/18.3.0>`_ (:download:`local-sig </../signatues/txtorcon-18.3.0.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-18.3.0.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v18.3.0.tar.gz>`_)
 * add `singleHop={true,false}` for endpoint-strings as well


v18.2.0
-------

 * `txtorcon-18.2.0.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-18.2.0.tar.gz>`_ (`PyPI <https://pypi.python.org/pypi/txtorcon/18.2.0>`_ (:download:`local-sig </../signatues/txtorcon-18.2.0.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-18.2.0.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v18.2.0.tar.gz>`_)
 * add `privateKeyFile=` option to endpoint parser (ticket 313)
 * use `privateKey=` option properly in endpoint parser
 * support `NonAnonymous` mode for `ADD_ONION` via `single_hop=` kwarg


v18.1.0
-------

September 26, 2018

 * `txtorcon-18.1.0.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-18.1.0.tar.gz>`_ (`PyPI <https://pypi.python.org/pypi/txtorcon/18.1.0>`_ (:download:`local-sig </../signatues/txtorcon-18.1.0.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-18.1.0.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v18.1.0.tar.gz>`_)
 * better error-reporting (include REASON and REMOTE_REASON if
   available) when circuit-builds fail (thanks `David Stainton
   <https://github.com/david415>`_)
 * more-robust detection of "do we have Python3" (thanks `Balint
   Reczey <https://github.com/rbalint>`_)
 * fix parsing of Unix-sockets for SOCKS
 * better handling of concurrent Web agent requests before SOCKS ports
   are known
 * allow fowarding to ip:port pairs for Onion services when using the
   "list of 2-tuples" method of specifying the remote vs local
   connections.


v18.0.2
-------

July 2, 2018

 * `txtorcon-18.0.2.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-18.0.2.tar.gz>`_ (`PyPI <https://pypi.python.org/pypi/txtorcon/18.0.2>`_ (:download:`local-sig </../signatues/txtorcon-18.0.2.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-18.0.2.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v18.0.2.tar.gz>`_)
 * Python3.4 doesn't support async-def or await


v18.0.1
-------

June 30, 2018

 * `txtorcon-18.0.1.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-18.0.1.tar.gz>`_ (`PyPI <https://pypi.python.org/pypi/txtorcon/18.0.1>`_ (:download:`local-sig </../signatues/txtorcon-18.0.1.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-18.0.1.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v18.0.1.tar.gz>`_)
 * fix a Python2/3 regression when parsing onion services


v18.0.0
-------

June 21, 2018

 * `txtorcon-18.0.0.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-18.0.0.tar.gz>`_ (`PyPI <https://pypi.python.org/pypi/txtorcon/18.0.0>`_ (:download:`local-sig </../signatues/txtorcon-18.0.0.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-18.0.0.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v18.0.0.tar.gz>`_)

 * `await_all_uploads` options when creating Onions
 * properly re-map progress percentages (including descriptor uploads)
 * properly wait for all event-listeners during startup
 * re-work how `TorState.event_map` works, hopefully reducing
   reproducible-builds issues
 * :meth:`txtorcon.TorControlProtocol.add_event_listener` and
   :meth:`txtorcon.TorControlProtocol.remove_event_listener` are now
   async methods returning Deferred -- they always should have been; new
   code can now be assured that the event-listener change is known to Tor
   by awaiting this Deferred.
 * :meth:`txtorcon.TorControlProtocol.get_conf_single` method added, which
   gets and returns (asynchronously) a single GETCONF key (instead of a dict)
 * also :meth:`txtorcon.TorControlProtocol.get_info_single` similar to above
 * if Tor disconnects while a command is in-progress or pending, the
   `.errback()` for the corresponding Deferred is now correctly fired
   (with a :class:`txtorcon.TorDisconnectError`

 * tired: `get_global_tor()` (now deprecated)
   wired: :meth:`txtorcon.get_global_tor_instance`

 * Adds a comprehensive set of Onion Services APIs (for all six
   variations). For non-authenticated services, instances of
   :class:`txtorcon.IOnionService` represent services; for
   authenticated services, instances of
   :class:`txtorcon.IAuthenticatedOnionClients` encapsulated named
   lists of clients (each client is an instance implementing
   `IOnionService`).
 * Version 3 ("Proposition 279") Onion service support (same APIs) as
   released in latest Tor
 * Four new methods to handle creating endpoints for Onion services
   (either ephemeral or not and authenticated or not):
   ** :method:`txtorcon.Tor.create_authenticated_onion_endpoint`
   ** :method:`txtorcon.Tor.create_authenticated_filesystem_onion_endpoint`
   ** :method:`txtorcon.Tor.create_onion_endpoint`
   ** :method:`txtorcon.Tor.create_filesystem_onion_endpoint`
 * see :ref:`create_onion` for information on how to choose an
   appropriate type of Onion Service.

 * :method:`txtorcon.Tor.create_onion_service` to add a new ephemeral
   Onion service to Tor. This uses the `ADD_ONION` command under the
   hood and can be version 2 or version 3. Note that there is an
   endpoint-style API as well so you don't have to worry about mapping
   ports yourself (see below).
 * :method:`txtorcon.Tor.create_filesystem_onion_service` to add a new
   Onion service to Tor with configuration (private keys) stored in a
   provided directory. These can be version 2 or version 3
   services. Note that there is an endpoint-style API as well so you
   don't have to worry about mapping ports yourself (see below).

 * Additional APIs to make visiting authenticated Onion services as a
   client easier:

 * :method:`txtorcon.Tor.add_onion_authentication` will add a
   client-side Onion service authentication token. If you add a token
   for a service which already has a token, it is an error if they
   don't match. This corresponds to `HidServAuth` lines in torrc.
 * :method:`txtorcon.Tor.remove_onion_authentication` will remove a
   previously added client-side Onion service authentication
   token. Fires with True if such a token existed and was removed or
   False if no existing token was found.
 * :method:`txtorcon.Tor.onion_authentication` (Python3 only) an async
   context-manager that adds and removes an Onion authentication token
   (i.e. adds in on `__aenter__` and removes it on `__aexit__`).
 * onion services support listening on Unix paths.
 * make sure README renders on Warehouse/PyPI


v0.20.0
-------

February 22, 2018

 * `txtorcon-0.20.0.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-0.20.0.tar.gz>`_ (`PyPI <https://pypi.python.org/pypi/txtorcon/0.20.0>`_ (:download:`local-sig </../signatues/txtorcon-0.20.0.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-0.20.0.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v0.20.0.tar.gz>`_)

 * doc fixes from `hotelzululima <https://twitter.com/hotelzululima>`_
 * fix endpoints so `.connect` on them works properly more than once
   from `Brian Warner <https://github.com/warner>`_
 * allow a `CertificateOptions` to be passed as `tls=` to endpoints
 * add method :func:`txtorcon.Tor.is_ready`
 * add method :func:`txtorcon.Tor.become_ready`
 * fix handling of certain defaults (`*PortLines` and friends)
 * fix last router (usually) missing with (new) `MicroDescriptorParser`
 * use OnionOO via Onion service `tgel7v4rpcllsrk2.onion` for :func:`txtorcon.Router.get_onionoo_details`
 * fix parsing of Router started-times
 * `Issue 255 <https://github.com/meejah/txtorcon/issues/255>`_ removed routers now deleted following NEWCONSENSUS
 * `Issue 279 <https://github.com/meejah/txtorcon/issues/279>`_ remember proxy endpoint


v0.19.3
-------

May 24, 2017

 * `txtorcon-0.19.3.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-0.19.3.tar.gz>`_ (`PyPI <https://pypi.python.org/pypi/txtorcon/0.19.3>`_ (:download:`local-sig </../signatues/txtorcon-0.19.3.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-0.19.3.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v0.19.3.tar.gz>`_)

 * Incorrect parsing of SocksPort options (see `Issue 237 <https://github.com/meejah/txtorcon/issues/237>`_)


v0.19.2
-------

May 11, 2017

 * `txtorcon-0.19.2.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-0.19.2.tar.gz>`_ (`PyPI <https://pypi.python.org/pypi/txtorcon/0.19.2>`_ (:download:`local-sig </../signatues/txtorcon-0.19.2.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-0.19.2.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v0.19.2.tar.gz>`_)

 * Work around a bug in `incremental` (see `Issue 233 <https://github.com/meejah/txtorcon/issues/233>`_)
 * Fix for `Issue 190 <https://github.com/meejah/txtorcon/issues/190>`_ from Felipe Dau.
 * add :meth:`txtorcon.Circuit.when_built`.


v0.19.1
-------

April 26, 2017

 * `txtorcon-0.19.1.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-0.19.1.tar.gz>`_ (`PyPI <https://pypi.python.org/pypi/txtorcon/0.19.1>`_ (:download:`local-sig </../signatues/txtorcon-0.19.1.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-0.19.1.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v0.19.1.tar.gz>`_)

 * Fix a regression in ``launch_tor``, see `Issue 227 <https://github.com/meejah/txtorcon/issues/227>`_


v0.19.0
-------

April 20, 2017

 * `txtorcon-0.19.0.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-0.19.0.tar.gz>`_ (`PyPI <https://pypi.python.org/pypi/txtorcon/0.19.0>`_ (:download:`local-sig </../signatues/txtorcon-0.19.0.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-0.19.0.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v0.19.0.tar.gz>`_)

 * Full Python3 support
 * Drop `txsocksx` and use a custom implementation (this also
   implements the custom Tor SOCKS5 methods RESOLVE and RESOLVE_PTR
 * Drop support for older Twisted releases (12, 13 and 14 are no
   longer supported).
 * Add a top-level API object, :class:`txtorcon.Tor` that abstracts a
   running Tor. Instances of this class are created with
   :meth:`txtorcon.connect` or :meth:`txtorcon.launch`. These
   instances are intended to be "the" high-level API and most users
   shouldn't need anything else.
 * Integrated support for `twisted.web.client.Agent`, baked into
   :class:`txtorcon.Tor`. This allows simple, straightforward use of
   treq_ or "raw" `twisted.web.client` for making client-type Web
   requests via Tor. Automatically handles configuration of SOCKS
   ports. See :meth:`txtorcon.Tor.web_agent`
 * new high-level API for putting streams on specific Circuits. This
   adds :meth:`txtorcon.Circuit.stream_via` and
   :meth:`txtorcon.Circuit.web_agent` methods that work the same as
   the "Tor" equivalent methods except they use a specific
   circuit. This makes :meth:`txtorcon.TorState.set_attacher` the
   "low-level" / "expert" interface. Most users should only need the
   new API.
 * big revamp / re-write of the documentation, including the new
   `Programming Guide
   <https://txtorcon.readthedocs.io/en/latest/guide.html>`_
 * `Issue 203 <https://github.com/meejah/txtorcon/issues/203>`_
 * new helper: :meth:`txtorcon.Router.get_onionoo_details`_
 * new helper: :func:`txtorcon.util.create_tbb_web_headers`_
 * `Issue 72 <https://github.com/meejah/txtorcon/issues/72>`_
 * `Felipe Dau <https://github.com/felipedau>`_ added specific
   `SocksError` subclasses for all the available SOCKS5 errors.
 * (more) Python3 fixes from `rodrigc <https://github.com/rodrigc>`_

.. _Automat: https://github.com/glyph/automat
.. _treq: https://pypi.python.org/pypi/treq


v0.18.0
-------

January 11, 2017

 * `txtorcon-0.18.0.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-0.18.0.tar.gz>`_ (`PyPI <https://pypi.python.org/pypi/txtorcon/0.18.0>`_ (:download:`local-sig </../signatues/txtorcon-0.18.0.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-0.18.0.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v0.18.0.tar.gz>`_)
 * `issue 200 <https://github.com/meejah/txtorcon/issues/200>`_: better feedback if the cookie data can't be read


v0.17.0
-------

*October 4, 2016*

 * `txtorcon-0.17.0.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-0.17.0.tar.gz>`_ (`PyPI <https://pypi.python.org/pypi/txtorcon/0.17.0>`_ (:download:`local-sig </../signatues/txtorcon-0.17.0.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-0.17.0.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v0.17.0.tar.gz>`_)
 * `issue 187 <https://github.com/meejah/txtorcon/issues/187>`_: fix unix-socket control endpoints
 * sometimes mapping streams to hostnames wasn't working properly
 * backwards-compatibility API for `socks_hostname` was incorrectly named


v0.16.1
-------

*August 31, 2016*

 * `txtorcon-0.16.1.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-0.16.1.tar.gz>`_ (`PyPI <https://pypi.python.org/pypi/txtorcon/0.16.1>`_ (:download:`local-sig </../signatues/txtorcon-0.16.1.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-0.16.1.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v0.16.1.tar.gz>`_)
 * `issue 172 <https://github.com/meejah/txtorcon/issues/172>`_: give `TorProcessProtocol` a `.quit` method
 * `issue 181 <https://github.com/meejah/txtorcon/issues/181>`_: enable SOCKS5-over-unix-sockets for TorClientEndpoint (thanks to `david415 <https://github.com/david415>`_


v0.16.0
-------

 * there wasn't one, `because reasons <https://github.com/meejah/txtorcon/commit/e4291c01ff223d3cb7774437cafa2f06ca195bcf>`_.


v0.15.1
-------

 * `txtorcon-0.15.1.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-0.15.1.tar.gz>`_ (`PyPI <https://pypi.python.org/pypi/txtorcon/0.15.1>`_ (:download:`local-sig </../signatues/txtorcon-0.15.1.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-0.15.1.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v0.15.1.tar.gz>`_)
 * fix `issue 179 <https://github.com/meejah/txtorcon/issues/179>`_ with `Circuit.age`.


v0.15.0
-------

*July 26, 2016*

 * `txtorcon-0.15.0.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-0.15.0.tar.gz>`_ (`PyPI <https://pypi.python.org/pypi/txtorcon/0.15.0>`_ (:download:`local-sig </../signatues/txtorcon-0.15.0.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-0.15.0.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v0.15.0.tar.gz>`_)
 * added support for NULL control-port-authentication which is often
   appropriate when used with a UNIX domain socket
 * switched to `ipaddress
   <https://docs.python.org/3/library/ipaddress.html>`_ instead of
   Google's ``ipaddr``; the API should be the same from a user
   perspective but **packagers and tutorials** will want to change
   their instructions slightly (``pip install ipaddress`` or ``apt-get
   install python-ipaddress`` are the new ways).
 * support the new ADD_ONION and DEL_ONION "ephemeral hidden services"
   commands in TorConfig
 * a first stealth-authentication implementation (for "normal" hidden
   services, not ephemeral)
 * bug-fix from `david415 <https://github.com/david415>`_ to raise
   ConnectionRefusedError instead of StopIteration when running out of
   SOCKS ports.
 * new feature from `david415 <https://github.com/david415>`_ adding a
   ``build_timeout_circuit`` method which provides a Deferred that
   callbacks only when the circuit is completely built and errbacks if
   the provided timeout expires. This is useful because
   :meth:`txtorcon.TorState.build_circuit` callbacks as soon as a Circuit
   instance can be provided (and then you'd use
   :meth:`txtorcon.Circuit.when_built` to find out when it's done building).
 * new feature from `coffeemakr <https://github.com/coffeemakr>`_
   falling back to password authentication if cookie authentication
   isn't available (or fails, e.g. because the file isn't readable).
 * both TorState and TorConfig now have a ``.from_protocol`` class-method.
 * spec-compliant string-un-escaping from `coffeemakr <https://github.com/coffeemakr>`_
 * a proposed new API: :meth:`txtorcon.connect`
 * fix `issue 176 <https://github.com/meejah/txtorcon/issues/176>`_


v0.14.2
-------

*December 2, 2015*

 * `txtorcon-0.14.2.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-0.14.2.tar.gz>`_ (`PyPI <https://pypi.python.org/pypi/txtorcon/0.14.2>`_ (:download:`local-sig </../signatues/txtorcon-0.14.2.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-0.14.2.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v0.14.2.tar.gz>`_)
 * compatibility for Twisted 15.5.0 (released on 0.14.x for `OONI <http://ooni.io/>`_)


v0.14.1
-------

*October 25, 2015*

 * subtle bug with ``.is_built`` on Circuit; changing the API (but
   with backwards-compatibility until 0.15.0 at least)


v0.14.0
-------

*September 26, 2015*

 * `txtorcon-0.14.0.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-0.14.0.tar.gz>`_ (`PyPI <https://pypi.python.org/pypi/txtorcon/0.14.0>`_ (:download:`local-sig </../signatues/txtorcon-0.14.0.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-0.14.0.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v0.14.0.tar.gz>`_)
 * :class:`txtorcon.interface.IStreamAttacher` handling was missing ``None`` and ``DO_NOT_ATTACH`` cases if a Deferred was returned.
 * add ``.is_built`` Deferred to :class:`txtorcon.Circuit` that gets `callback()`d when the circuit becomes BUILT
 * `david415 <https://github.com/david415>`_ ported his ``tor:``
   endpoint parser so now both client and server endpoints are
   supported. This means **any** Twisted program using endpoints can
   use Tor as a client. For example, to connect to txtorcon's Web site:
   ``ep = clientFromString("tor:timaq4ygg2iegci7.onion:80")``.
   (In the future, I'd like to automatically launch Tor if required, too).
 * Python3 fixes from `isis <https://github.com/isislovecruft>`_ (note: needs Twisted 15.4.0+)


v0.13.0
-------

*May 10, 2015*

 * `txtorcon-0.13.0.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-0.13.0.tar.gz>`_ (`PyPI <https://pypi.python.org/pypi/txtorcon/0.13.0>`_ (:download:`local-sig </../signatues/txtorcon-0.13.0.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-0.13.0.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v0.13.0.tar.gz>`_)
 * support ``basic`` and ``stealth`` hidden service authorization, and parse ``client_keys`` files.
 * 2x speedup for TorState parsing (mostly by lazy-parsing timestamps)
 * can now parse ~75000 microdescriptors/second per core of 3.4GHz Xeon E3
 * ``launch_tor`` now doesn't use a temporary ``torrc`` (command-line options instead)
 * tons of pep8 cleanups
 * several improvements to hidden-service configuration from `sambuddhabasu1`_.
 * populated valid signals from ``GETINFO signals/names`` from `sambuddhabasu1`_.

.. _sambuddhabasu1: https://github.com/sammyshj


v0.12.0
-------

*February 3, 2015*

 * `txtorcon-0.12.0.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-0.12.0.tar.gz>`_ (`PyPI <https://pypi.python.org/pypi/txtorcon/0.12.0>`_ (:download:`local-sig </../signatues/txtorcon-0.12.0.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-0.12.0.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v0.12.0.tar.gz>`_)
 * doc, code and import cleanups from `Kali Kaneko <https://github.com/kalikaneko>`_
 * HiddenServiceDirGroupReadable support
 * Issue #80: honour ``ControlPort 0`` in incoming TorConfig
   instance. The caller owns both pieces: you have to figure out when
   it's bootstraped, and are responsible for killing it off.
 * Issue #88: clarify documentation and fix appending to some config lists
 * If GeoIP data isn't loaded in Tor, it sends protocol errors; if
   txtorcon also hasn't got GeoIP data, the queries for country-code
   fail; this error is now ignored.
 * **100% unit-test coverage!** (line coverage)
 * PyPy support (well, at least all tests pass)
 * TCP4HiddenServiceEndpoint now waits for descriptor upload before
   the ``listen()`` call does its callback (this means when using
   ``onion:`` endpoint strings, or any of the :doc:`endpoints APIs
   <txtorcon-endpoints>` your hidden service is 100% ready for action
   when you receive the callback)
 * ``TimeIntervalCommaList`` from Tor config supported
 * :class:`TorControlProtocol <txtorcon.TorControlProtocol>` now has a ``.all_routers`` member (a ``set()`` of all Routers)
 * documentation fix from `sammyshj <https://github.com/sammyshj>`_


v0.11.0
-------

*August 16, 2014*

 * September 6, 2015. bugfix release: `txtorcon-0.11.1.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-0.11.1.tar.gz>`_ (`PyPI <https://pypi.python.org/pypi/txtorcon/0.11.1>`_ (:download:`local-sig </../signatues/txtorcon-0.11.1.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-0.11.1.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v0.11.1.tar.gz>`_)
 * fixed Debian bug `797261 <https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=797261>`_ causing 3 tests to fail
 * `txtorcon-0.11.0.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-0.11.0.tar.gz>`_ (`PyPI <https://pypi.python.org/pypi/txtorcon/0.11.0>`_ (:download:`local-sig </../signatues/txtorcon-0.11.0.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-0.11.0.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v0.11.0.tar.gz>`_) 
 * More control for ``launch_tor``: access stdout, stderr in real-time
   and control whether we kill Tor on and stderr output. See issue #79.
 * Warning about ``build_circuit`` being called without a guard first
   is now optional (default is still warn) (from arlolra_)
 * ``available_tcp_port()`` now in util (from arlolra_)
 * ``TorState`` now has a ``.routers_by_hash`` member (from arlolra_)

.. _arlolra: https://github.com/arlolra

v0.10.1
-------

*July 20, 2014*

 * `txtorcon-0.10.1.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-0.10.1.tar.gz>`_ (`PyPI <https://pypi.python.org/pypi/txtorcon/0.10.1>`_ (:download:`local-sig </../signatues/txtorcon-0.10.1.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-0.10.1.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v0.10.1.tar.gz>`_) 
 * fix bug incorrectly issuing RuntimeError in brief window of time on event-listeners
 * issue #78: Add tox tests and fix for Twisted 12.0.0 (and prior), as this is what Debian squeeze ships
 * issue #77: properly expand relative and tilde paths for ``hiddenServiceDir`` via endpoints


v0.10.0
-------

*June 15, 2014*

 * `txtorcon-0.10.0.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-0.10.0.tar.gz>`_ (`PyPI <https://pypi.python.org/pypi/txtorcon/0.10.0>`_ (:download:`local-sig </../signatues/txtorcon-0.10.0.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-0.10.0.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v0.10.0.tar.gz>`_)
 * In collaboration with `David Stainton <https://github.com/david415>`_ after a pull-request, we
   have endpoint parser plugins for Twisted! This means code like
   ``serverFromString("onion:80").listen(...)`` is enough to start a
   service.
 * The above **also** means that **any** endpoint-using Twisted program can immediately offer its TCP services via Hidden Service with **no code changes**.    For example, using Twisted Web to serve a WSGI web application would be simply: ``twistd web --port onion:80 --wsgi web.app``
 * switch to a slightly-modified `Alabaster Sphinx theme <https://github.com/bitprophet/alabaster>`_
 * added howtos to documentation


v0.9.2
------

*April 23, 2014*

 * `txtorcon-0.9.2.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-0.9.2.tar.gz>`_ (:download:`local-sig </../signatues/txtorcon-0.9.2.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-0.9.2.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v0.9.2.tar.gz>`_)
 * add ``on_disconnect`` callback for TorControlProtocol (no more monkey-patching Protocol API)
 * add ``age()`` method to Circuit
 * add ``time_created`` property to Circuit
 * don't incorrectly listen for NEWDESC events in TorState
 * add ``.flags`` dict to track flags in Circuit, Stream
 * ``build_circuit()`` can now take hex IDs (as well as Router instances)
 * add ``unique_name`` property to Router (returns the hex id, unless ``Named`` then return name)
 * add ``location`` property to Router
 * ``TorState.close_circuit`` now takes either a Circuit ID or Circuit instance
 * ``TorState.close_stream`` now takes either a Stream ID or Stream instance
 * support both GeoIP API versions
 * more test-coverage
 * small patch from `enriquefynn <https://github.com/enriquefynn>`_ improving ``tor`` binary locating
 * strip OK lines in TorControlProtocol (see `issue #8 <https://github.com/meejah/txtorcon/issues/8>`_)
 * use TERM not KILL when Tor launch times out (see `issue #68 <https://github.com/meejah/txtorcon/pull/68>`_) from ``hellais``


v0.9.1
------

*January 20, 2014*

 * `txtorcon-0.9.1.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-0.9.1.tar.gz>`_ (:download:`local-sig </../signatues/txtorcon-0.9.1.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-0.9.1.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v0.9.1.tar.gz>`_)
 * put test/ directory at the top level
 * using "`coverage <http://nedbatchelder.com/code/coverage/>`_" tool instead of custom script
 * using `coveralls.io <https://coveralls.io/r/meejah/txtorcon>`_ and `travis-ci <https://travis-ci.org/meejah/txtorcon>`_ for test coverage and continuous integration
 * `issue #56 <https://github.com/meejah/txtorcon/issues/56>`_: added Circuit.close() and Stream.close() starting from aagbsn's patch
 * parsing issues with multi-line keyword discovered and resolved
 * preserve router nicks from long-names if consensus lacks an entry (e.g. bridges)
 * using `Twine <https://github.com/dstufft/twine>`_ for releases
 * `Wheel <http://wheel.readthedocs.org/en/latest/>`_ release now also available
 * `issue #57 <https://github.com/meejah/txtorcon/issues/57>`_: "python setup.py develop" now supported
 * `issue #59 <https://github.com/meejah/txtorcon/pull/59>`_: if tor_launch() times out, Tor is properly killed (starting with pull-request from Ryman)
 * experimental docker.io-based tests (for HS listening, and tor_launch() timeouts)
 * `issue #55 <https://github.com/meejah/txtorcon/issues/55>`_: pubkey link on readthedocs
 * `issue #63 <https://github.com/meejah/txtorcon/issues/55>`_
 * clean up GeoIP handling, and support pygeoip both pre and post 0.3
 * slightly improve unit-test coverage (now at 97%, 61 lines of 2031 missing)
 * added a `Walkthrough <walkthrough.html>`_ to the documentation


v0.8.2
------

*November 22, 2013*

 * `txtorcon-0.8.2.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-0.8.2.tar.gz>`_ (:download:`local-sig </../signatues/txtorcon-0.8.2.tar.gz.asc>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-0.8.2.tar.gz.asc?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v0.8.2.tar.gz>`_)
 * ensure hidden service server-side endpoints listen only on 127.0.0.1


v0.8.1
------

*May 13, 2013*

 * `txtorcon-0.8.1.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-0.8.1.tar.gz>`_ (:download:`local-sign </../signatues/txtorcon-0.8.1.tar.gz.sig>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-0.8.1.tar.gz.sig?raw=true>`_) (`source <https://github.com/meejah/txtorcon/archive/v0.8.1.tar.gz>`_)
 * fixed improper import in setup.py preventing 0.8.0 from installing
 * signatures with proper subkey this time
 * Proper file-flushing in tests and PyPy fixes from Lukas Lueg
 * docs build issue from isis

v0.8.0
------

*April 11, 2013* (actually uploaded May 11)

 * **Please use 0.8.1; this won't install due to import problem in setup.py (unless you have pypissh).**
 * following `semantic versioning <http://semver.org/>`_;
 * slight **API change** :meth:`.ICircuitListener.circuit_failed`, :meth:`~.ICircuitListener.circuit_closed` and :meth:`.IStreamListener.stream_failed`, :meth:`~.IStreamListener.stream_closed` and :meth:`~.IStreamListener.stream_detach` all now include any keywords in the notification method (some of these lacked flags, or only included some) (`issue #18 <https://github.com/meejah/txtorcon/issues/18>`_);
 * launch_tor() can take a timeout (starting with a patch from hellais);
 * cleanup from aagbsn;
 * more test coverage;
 * run tests cleanly without graphviz (from lukaslueg);
 * `issue #26 <https://github.com/meejah/txtorcon/issues/26>`_ fix from lukaslueg;
 * pep8 and whitespace targets plus massive cleanup (now pep8 clean, from lukaslueg);
 * `issue #30 <https://github.com/meejah/txtorcon/issues/30>`_ fix reported by webmeister making ipaddr actually-optional;
 * example using synchronous web server (built-in SimpleHTTPServer) with txtorcon (from lukaslueg);
 * TorState can now create circuits without an explicit path;
 * passwords for non-cookie authenticated sessions use a password callback (that may return a Deferred) instead of a string (`issue #44 <https://github.com/meejah/txtorcon/issues/44>`_);
 * fixes for AddrMap in case `#8596 <https://trac.torproject.org/projects/tor/ticket/8596>`_ is implemented;

v0.7
----

*November 21, 2012*

 * `txtorcon-0.7.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-0.7.tar.gz>`_ (:download:`local-sig <../signatues/txtorcon-0.7.tar.gz.sig>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-0.7.tar.gz.sig?raw=true>`_) (`source <https://github.com/meejah/txtorcon/tarball/v0.7>`_)
 * `issue #20 <https://github.com/meejah/txtorcon/issues/20>`_ config object now hooked up correctly after launch_tor();
 * `patch <https://github.com/meejah/txtorcon/pull/22>`_ from hellais for properly handling data_dir given to TCPHiddenServiceEndpoint;
 * `.tac example <https://github.com/meejah/txtorcon/pull/19>`_ from mmaker;
 * allow TorConfig().hiddenservices.append(hs) to work properly with no attached protocol

v0.6
----

*October 10, 2012*

 * `txtorcon-0.6.tar.gz <http://timaq4ygg2iegci7.onion/txtorcon-0.6.tar.gz>`_ (:download:`local-sig <../signatues/txtorcon-0.6.tar.gz.sig>` or `github-sig <https://github.com/meejah/txtorcon/blob/master/signatues/txtorcon-0.6.tar.gz.sig?raw=true>`_) (`source <https://github.com/meejah/txtorcon/tarball/v0.6>`_)
 * debian packaging (mmaker);
 * psutil fully gone;
 * *changed API* for launch_tor() to use TorConfig instead of args;
 * TorConfig.save() works properly with no connected Tor;
 * fix incorrect handling of 650 immediately after connect;
 * `pep8 compliance <http://www.python.org/dev/peps/pep-0008/>`_;
 * use assertEqual in tests;
 * messages with embdedded keywords work properly;
 * fix bug with setup.py + pip;
 * `issue #15 <https://github.com/meejah/txtorcon/issues/15>`_ reported along with patch by `Isis Lovecruft <https://github.com/isislovecruft>`_;
 * consolidate requirements (from `aagbsn <https://github.com/aagbsn>`_);
 * increased test coverage and various minor fixes;
 * https URIs for ReadTheDocs;

v0.5
----
June 20, 2012

 * `txtorcon-0.5.tar.gz <txtorcon-0.5.tar.gz>`_ (`txtorcon-0.5.tar.gz.sig <txtorcon-0.5.tar.gz.sig>`_) (`source <https://github.com/meejah/txtorcon/tarball/v0.5>`_)
 * remove psutil as a dependency, including from `util.process_from_address`

v0.4
----
June 6, 2012

 * `txtorcon-0.4.tar.gz <txtorcon-0.4.tar.gz>`_ (`txtorcon-0.4.tar.gz.sig <txtorcon-0.4.tar.gz.sig>`_)
 * remove built documentation from distribution; 
 * fix PyPI problems ("pip install txtorcon" now works)

v0.3
----
 * 0.3 was broken when released (docs couldn't build).

v0.2
----
June 1, 2012

 * `txtorcon-0.2.tar.gz <txtorcon-0.2.tar.gz>`_ (`txtorcon-0.2.tar.gz.sig <txtorcon-0.2.tar.gz.sig>`_)
 * incremental parsing;
 * faster TorState startup;
 * SAFECOOKIE support;
 * several bug fixes;
 * options to `circuit_failure_rates.py` example to make it actually-useful;
 * include built documentation + sources in tarball;
 * include tests in tarball;
 * improved logging;
 * patches from `mmaker <https://github.com/mmaker>`_ and `kneufeld <https://github.com/kneufeld>`_;

v0.1
----
march, 2012

 * `txtorcon-0.1.tar.gz <txtorcon-0.1.tar.gz>`_ (`txtorcon-0.1.tar.gz.sig <txtorcon-0.1.tar.gz.sig>`_)

