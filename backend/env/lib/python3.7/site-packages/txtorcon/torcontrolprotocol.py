# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function
from __future__ import with_statement

import os
import re
import base64
from binascii import b2a_hex, hexlify

from twisted.python import log
from twisted.internet import defer
from twisted.internet.interfaces import IProtocolFactory
from twisted.internet.error import ConnectionDone
from twisted.protocols.basic import LineOnlyReceiver
from twisted.python.failure import Failure

from zope.interface import implementer

from txtorcon.util import hmac_sha256, compare_via_hash, unescape_quoted_string
from txtorcon.log import txtorlog

from txtorcon.interface import ITorControlProtocol
from .spaghetti import FSM, State, Transition
from .util import maybe_coroutine


DEFAULT_VALUE = 'DEFAULT'


class TorProtocolError(RuntimeError):
    """
    Happens on 500-level responses in the protocol, almost certainly
    in an errback chain.

    :ivar code: the actual error code
    :ivar text: other text from the protocol
    """

    def __init__(self, code, text):
        self.code = code
        self.text = text
        super(TorProtocolError, self).__init__(text)

    def __str__(self):
        return str(self.code) + ' ' + self.text


class TorDisconnectError(RuntimeError):
    """
    Happens when Tor disconnects unexpectedly (i.e. while commands are pending)

    :ivar text: a human-readable description of the error
    :ivar error: the Failure instance that connectionLost received
    """

    def __init__(self, text, error):
        self.text = text
        self.error = error
        super(TorDisconnectError, self).__init__(text)

    def __str__(self):
        return self.text


@implementer(IProtocolFactory)
class TorProtocolFactory(object):
    """
    Builds TorControlProtocol objects. Implements IProtocolFactory for
    Twisted interaction.

    If your running Tor doesn't support COOKIE authentication, then
    you should supply a password callback.
    """

    def __init__(self, password_function=lambda: None):
        """
        Builds protocols to talk to a Tor client on the specified
        address. For example::

            ep = TCP4ClientEndpoint(reactor, "localhost", 9051)
            ep.connect(TorProtocolFactory())
            reactor.run()

        By default, COOKIE authentication is used if
        available.

        :param password_function:
           If supplied, this is a zero-argument method that returns a
           password (or a Deferred). By default, it returns None. This
           is only queried if the Tor we connect to doesn't support
           (or hasn't enabled) COOKIE authentication.
        """
        self.password_function = password_function

    def doStart(self):
        ":api:`twisted.internet.interfaces.IProtocolFactory` API"

    def doStop(self):
        ":api:`twisted.internet.interfaces.IProtocolFactory` API"

    def buildProtocol(self, addr):
        ":api:`twisted.internet.interfaces.IProtocolFactory` API"
        proto = TorControlProtocol(self.password_function)
        proto.factory = self
        return proto


class Event(object):
    """
    A class representing one of the valid EVENTs that Tor
    supports.

    This allows you to listen for such an event; see
    TorController.add_event The callbacks will be called every time
    the event in question is received.
    """
    def __init__(self, name):
        self.name = name
        self.callbacks = []

    def listen(self, cb):
        self.callbacks.append(cb)

    def unlisten(self, cb):
        self.callbacks.remove(cb)

    def got_update(self, data):
        for cb in self.callbacks:
            try:
                cb(data)
            except Exception as e:
                log.err(Failure())
                log.err(
                    "Notifying '{callback}' for '{name}' failed: {e}".format(
                        callback=cb,
                        name=self.name,
                        e=e,
                    )
                )


def unquote(word):
    if len(word) == 0:
        return word
    if word[0] == '"' and word[-1] == '"':
        return word[1:-1]
    elif word[0] == "'" and word[-1] == "'":
        return word[1:-1]
    return word


def parse_keywords(lines, multiline_values=True, key_hints=None):
    """
    Utility method to parse name=value pairs (GETINFO etc). Takes a
    string with newline-separated lines and expects at most one = sign
    per line. Accumulates multi-line values.

    :param multiline_values:
        The default is True which allows for multi-line values until a
        line with the next = sign on it. So: '''Foo=bar\nBar'''
        produces one key, 'Foo', with value 'bar\nBar' -- set to
        False, there would be two keys: 'Foo' with value 'bar' and
        'Bar' with value DEFAULT_VALUE.
    """

    rtn = {}
    key = None
    value = ''
    # FIXME could use some refactoring to reduce code duplication!
    for line in lines.split('\n'):
        if line.strip() == 'OK':
            continue

        sp = line.split('=', 1)
        found_key = ('=' in line and ' ' not in sp[0])
        if found_key and key_hints and sp[0] not in key_hints:
            found_key = False
        if found_key:
            if key:
                if key in rtn:
                    if isinstance(rtn[key], list):
                        rtn[key].append(unquote(value))
                    else:
                        rtn[key] = [rtn[key], unquote(value)]
                else:
                    rtn[key] = unquote(value)
            (key, value) = line.split('=', 1)

        else:
            if key is None:
                rtn[line.strip()] = DEFAULT_VALUE

            elif multiline_values is False:
                rtn[key] = value
                rtn[line.strip()] = DEFAULT_VALUE
                key = None
                value = ''

            else:
                value = value + '\n' + line
    if key:
        if key in rtn:
            if isinstance(rtn[key], list):
                rtn[key].append(unquote(value))
            else:
                rtn[key] = [rtn[key], unquote(value)]
        else:
            rtn[key] = unquote(value)
    return rtn


@implementer(ITorControlProtocol)
class TorControlProtocol(LineOnlyReceiver):
    """
    This is the main class that talks to a Tor and implements the "raw"
    procotol.

    This instance does not track state; see :class:`txtorcon.TorState`
    for the current state of all Circuits, Streams and Routers.

    :meth:`txtorcon.TorState.build_circuit` allows you to build custom
    circuits.

    :meth:`txtorcon.TorControlProtocol.add_event_listener` can be used
    to listen for specific events.

    To see how circuit and stream listeners are used, see
    :class:`txtorcon.TorState`, which is also the place to go if you
    wish to add your own stream or circuit listeners.
    """

    def __init__(self, password_function=None):
        """
        :param password_function:
            A zero-argument callable which returns a password (or
            Deferred). It is only called if the Tor doesn't have
            COOKIE authentication turned on. Tor's default is COOKIE.
        """

        self.password_function = password_function
        """If set, a callable to query for a password to use for
        authentication to Tor (default is to use COOKIE, however). May
        return Deferred."""

        self._cookie_data = None
        """Data read from cookie file used to authenticate."""

        self.version = None
        """Version of Tor we've connected to."""

        self.is_owned = None
        """If not None, this is the PID of the Tor process we own
        (TAKEOWNERSHIP, etc)."""

        self.events = {}
        """events we've subscribed to (keyed by name like "GUARD", "STREAM")"""

        self.valid_events = {}
        """all valid events (name -> Event instance)"""

        self.valid_signals = []
        """A list of all valid signals we accept from Tor"""

        # XXX bad practice; this should be like an on_disconnct()
        # method that returns a new Deferred each time...
        self.on_disconnect = defer.Deferred()
        """
        This Deferred is triggered when the connection is closed. If
        there was an error, the errback is called instead.
        """

        self.post_bootstrap = defer.Deferred()
        """
        This Deferred is triggered when we're done setting up
        (authentication, getting information from Tor). You will want
        to use this to do things with the :class:`TorControlProtocol`
        class when it's set up, like::

            def setup_complete(proto):
                print "Setup complete, attached to Tor version",proto.version

            def setup(proto):
                proto.post_bootstrap.addCallback(setup_complete)

            ep = TCP4ClientEndpoint(reactor, "localhost", 9051)
            ep.connect(TorProtocolFactory())
            d.addCallback(setup)

        See the helper method :func:`txtorcon.build_tor_connection`.
        """

        # variables related to the state machine
        self.defer = None        # Deferred we returned for the current command
        self.response = ''
        self.code = None
        self.command = None      # currently processing this command
        self.commands = []       # queued commands

        # Here we build up the state machine. Mostly it's pretty
        # simply, confounded by the fact that 600's (notify) can come
        # at any time AND can be multi-line itself. Luckily, these
        # can't be nested, nor can the responses be interleaved.

        idle = State("IDLE")
        recv = State("RECV")
        recvmulti = State("RECV_PLUS")
        recvnotify = State("NOTIFY_MULTILINE")

        idle.add_transition(Transition(idle,
                                       self._is_single_line_response,
                                       self._broadcast_response))
        idle.add_transition(Transition(recvmulti,
                                       self._is_multi_line,
                                       self._start_command))
        idle.add_transition(Transition(recv,
                                       self._is_continuation_line,
                                       self._start_command))

        recv.add_transition(Transition(recvmulti,
                                       self._is_multi_line,
                                       self._accumulate_response))
        recv.add_transition(Transition(recv,
                                       self._is_continuation_line,
                                       self._accumulate_response))
        recv.add_transition(Transition(idle,
                                       self._is_finish_line,
                                       self._broadcast_response))

        recvmulti.add_transition(Transition(recv,
                                            self._is_end_line,
                                            lambda x: None))
        recvmulti.add_transition(Transition(recvmulti,
                                            self._is_not_end_line,
                                            self._accumulate_multi_response))

        self.fsm = FSM([recvnotify, idle, recvmulti, recv])
        self.state_idle = idle
        # hand-set initial state default start state is first in the
        # list; the above looks nice in dotty though
        self.fsm.state = idle
        self.stop_debug()

    def start_debug(self):
        self.debuglog = open('txtorcon-debug.log', 'w')

    def stop_debug(self):
        def noop(*args, **kw):
            pass

        class NullLog(object):
            write = noop
            flush = noop
        self.debuglog = NullLog()

    def graphviz_data(self):
        return self.fsm.dotty()

    # see end of file for all the state machine matcher and
    # transition methods.

    def get_info_raw(self, *args):
        """
        Mostly for internal use; gives you the raw string back from the
        GETINFO command. See :meth:`getinfo
        <txtorcon.TorControlProtocol.get_info>`
        """
        return self.queue_command('GETINFO %s' % ' '.join(args))

    def get_info_incremental(self, key, line_cb):
        """
        Mostly for internal use; calls GETINFO for a single key and
        calls line_cb with each line received, as it is received.

        See :meth:`getinfo <txtorcon.TorControlProtocol.get_info>`
        """

        def strip_ok_and_call(line):
            if line.strip() != 'OK':
                line_cb(line)
        return self.queue_command('GETINFO %s' % key, strip_ok_and_call)

    # The following methods are the main TorController API and
    # probably the most interesting for users.

    def get_info(self, *args):
        """
        Uses GETINFO to obtain informatoin from Tor.

        :param args:
            should be a list or tuple of strings which are valid
            information keys. For valid keys, see control-spec.txt
            from torspec.

            .. todo:: make some way to automagically obtain valid
                keys, either from running Tor or parsing control-spec

        :return:
            a ``Deferred`` which will callback with a dict containing
            the keys you asked for. If you want to avoid the parsing
            into a dict, you can use get_info_raw instead.
        """
        d = self.get_info_raw(*args)
        d.addCallback(parse_keywords, key_hints=args)
        return d

    def get_info_single(self, key):
        """
        Uses GETINFO to obtain informatoin from Tor.

        :param key:
            the name of a GETINFO key to retrieve. For valid keys, see
            control-spec.txt from torspec.

        :return:
            a ``Deferred`` which will callback with the value for that
            key (a string).
        """
        d = self.get_info_raw(key)
        d.addCallback(parse_keywords, key_hints=[key])
        d.addCallback(lambda values: values[key])
        return d

    def get_conf(self, *args):
        """
        Uses GETCONF to obtain configuration values from Tor.

        :param args: any number of strings which are keys to get. To
            get all valid configuraiton names, you can call:
            ``get_info('config/names')``

        :return: a Deferred which callbacks with one or many
            configuration values (depends on what you asked for). See
            control-spec for valid keys (you can also use TorConfig which
            will come set up with all the keys that are valid). The value
            will be a dict.

        Note that Tor differentiates between an empty value and a
        default value; in the raw protocol one looks like '250
        MyFamily' versus '250 MyFamily=' where the latter is set to
        the empty string and the former is a default value. We
        differentiate these by setting the value in the dict to
        DEFAULT_VALUE for the default value case, or an empty string
        otherwise.
        """

        d = self.queue_command('GETCONF %s' % ' '.join(args))
        d.addCallback(parse_keywords).addErrback(log.err)
        return d

    def get_conf_single(self, key):
        """
        Uses GETCONF to obtain configuration values from Tor.

        :param key: a key whose CONF value to retrieve. To
            get all valid configuraiton names, you can call:
            ``get_info('config/names')``

        :return: a Deferred which callbacks with the configuration value.

        Note that Tor differentiates between an empty value and a
        default value; in the raw protocol one looks like '250
        MyFamily' versus '250 MyFamily=' where the latter is set to
        the empty string and the former is a default value. We
        differentiate these by returning DEFAULT_VALUE for the default
        value case, or an empty string otherwise.
        """

        d = self.queue_command('GETCONF {}'.format(key))
        d.addCallback(parse_keywords).addErrback(log.err)
        # d.addCallback(lambda kw: kw[key])  # extract key we asked for initially
        # ...but, the key can have a different string-name because Tor
        # will return *it's* representation (e.g. can ask for
        # SOCKSPORT but it will tell you SocksPort=9050)
        d.addCallback(lambda kw: list(kw.values())[0])
        return d

    def get_conf_raw(self, *args):
        """
        Same as get_conf, except that the results are not parsed into a dict
        """

        return self.queue_command('GETCONF %s' % ' '.join(args))

    def set_conf(self, *args):
        """
        set configuration values. see control-spec for valid
        keys. args is treated as a list containing name then value
        pairs. For example, ``set_conf('foo', 'bar')`` will (attempt
        to) set the key 'foo' to value 'bar'.

        :return: a ``Deferred`` that will callback with the response
            ('OK') or errback with the error code and message (e.g.
            ``"552 Unrecognized option: Unknown option 'foo'.  Failing."``)
        """
        if len(args) % 2:
            d = defer.Deferred()
            d.errback(RuntimeError("Expected an even number of arguments."))
            return d
        strargs = [str(x) for x in args]
        keys = [strargs[i] for i in range(0, len(strargs), 2)]
        values = [strargs[i] for i in range(1, len(strargs), 2)]

        def maybe_quote(s):
            if ' ' in s:
                return '"%s"' % s
            return s
        values = [maybe_quote(v) for v in values]
        args = ' '.join(map(lambda x, y: '%s=%s' % (x, y), keys, values))
        return self.queue_command('SETCONF ' + args)

    def signal(self, nm):
        """
        Issues a signal to Tor. See control-spec or
        :attr:`txtorcon.TorControlProtocol.valid_signals` for which ones
        are available and their return values.

        :return: a ``Deferred`` which callbacks with Tor's response
            (``OK`` or something like ``552 Unrecognized signal code "foo"``).
        """
        if nm not in self.valid_signals:
            raise RuntimeError("Invalid signal " + nm)
        return self.queue_command('SIGNAL %s' % nm)

    # XXX FIXME this should have been async all along :/
    def add_event_listener(self, evt, callback):
        """
        Add a listener to an Event object. This may be called multiple
        times for the same event. If it's the first listener, a new
        SETEVENTS call will be initiated to Tor.

        :param evt: event name, see also
            :attr:`txtorcon.TorControlProtocol.events` .keys(). These
            event names are queried from Tor (with `GETINFO events/names`)

        :param callback: any callable that takes a single argument
             which receives the text collected for the event from the
             tor control protocol.

        For more information on the events supported, see
        `control-spec section 4.1
        <https://gitweb.torproject.org/torspec.git/tree/control-spec.txt#n1260>`_

        .. note::
            this is a low-level interface; if you want to follow
            circuit or stream creation etc. see TorState and methods
            like add_circuit_listener

        :returns: a Deferred that fires when the listener is added
            (this may involve a controller command if this is the first
            listener for this event).

        .. todo::
            - should have an interface for the callback
            - show how to tie in Stem parsing if you want
        """

        if evt not in self.valid_events.values():
            try:
                evt = self.valid_events[evt]
            except KeyError:
                raise RuntimeError("Unknown event type: " + evt)

        if evt.name not in self.events:
            self.events[evt.name] = evt
            d = self.queue_command('SETEVENTS %s' % ' '.join(self.events.keys()))
        else:
            d = defer.succeed(None)
        evt.listen(callback)
        return d

    # XXX this should have been async all along
    def remove_event_listener(self, evt, cb):
        """
        The opposite of :meth:`TorControlProtocol.add_event_listener`

        :param evt: the event name (or an Event object)

        :param cb: the callback object to remove

        :returns: a Deferred that fires when the listener is removed
            (this may involve a controller command if this is the last
            listener for this event).
        """
        if evt not in self.valid_events.values():
            # this lets us pass a string or a real event-object
            try:
                evt = self.valid_events[evt]
            except KeyError:
                raise RuntimeError("Unknown event type: " + evt)

        evt.unlisten(cb)
        if len(evt.callbacks) == 0:
            # note there's a slight window here for an event of this
            # type to come in before the SETEVENTS succeeds; see
            # _handle_notify which explicitly ignore this case.
            del self.events[evt.name]
            return self.queue_command('SETEVENTS %s' % ' '.join(self.events.keys()))
        else:
            return defer.succeed(None)

    def protocolinfo(self):
        """
        :return: a Deferred which will give you PROTOCOLINFO; see control-spec
        """

        return self.queue_command("PROTOCOLINFO 1")

    def authenticate(self, passphrase):
        """
        Call the AUTHENTICATE command.

        Quoting torspec/control-spec.txt: "The authentication token
        can be specified as either a quoted ASCII string, or as an
        unquoted hexadecimal encoding of that same string (to avoid
        escaping issues)."
        """
        if not isinstance(passphrase, bytes):
            passphrase = passphrase.encode()
        phrase = b2a_hex(passphrase)
        return self.queue_command(b'AUTHENTICATE ' + phrase)

    def quit(self):
        """
        Sends the QUIT command, which asks Tor to hang up on this
        controller connection.

        If you've taken ownership of the Tor to which you're
        connected, this should also cause it to exit. Otherwise, it
        won't.
        """
        return self.queue_command('QUIT')

    def queue_command(self, cmd, arg=None):
        """
        returns a Deferred which will fire with the response data when
        we get it

        Note that basically every request is ultimately funelled
        through this command.
        """

        if not isinstance(cmd, bytes):
            cmd = cmd.encode('ascii')
        d = defer.Deferred()
        self.commands.append((d, cmd, arg))
        self._maybe_issue_command()
        return d

    # the remaining methods are internal API implementations,
    # callbacks and state-tracking methods -- you shouldn't have any
    # need to call them.

    def lineReceived(self, line):
        """
        :api:`twisted.protocols.basic.LineOnlyReceiver` API
        """

        self.debuglog.write(line + b'\n')
        self.debuglog.flush()
        self.fsm.process(line.decode('ascii'))

    def connectionMade(self):
        "Protocol API"
        txtorlog.msg('got connection, authenticating')
        # XXX this Deferred is just being dropped on the floor
        d = self.protocolinfo()
        d.addCallback(self._do_authenticate)
        d.addErrback(self._auth_failed)

    def connectionLost(self, reason):
        "Protocol API"
        txtorlog.msg('connection terminated: ' + str(reason))
        # ...and this is why we don't do on_disconnect = Deferred() :(
        # and instead should have had on_disconnect() method that
        # returned a new Deferred to each caller..(we're checking if
        # this Deferred has any callbacks because if it doesn't we'll
        # generate an "Unhandled error in Deferred")
        if not self.on_disconnect.called and self.on_disconnect.callbacks:
            if reason.check(ConnectionDone):
                self.on_disconnect.callback(self)
            else:
                self.on_disconnect.errback(reason)
        self.on_disconnect = None
        outstanding = [self.command] + self.commands if self.command else self.commands
        for d, cmd, cmd_arg in outstanding:
            if not d.called:
                d.errback(
                    Failure(
                        TorDisconnectError(
                            text=("Tor unexpectedly disconnected while "
                                  "running: {}".format(cmd.decode('ascii'))),
                            error=reason,
                        )
                    )
                )
        return None

    def _handle_notify(self, code, rest):
        """
        Internal method to deal with 600-level responses.
        """

        firstline = rest[:rest.find('\n')]
        args = firstline.split()
        name = args[0]
        if name in self.events:
            self.events[name].got_update(rest[len(name) + 1:])
            return
        # not considering this an error, as there's a slight window
        # after remove_event_listener is called (so the handler is
        # deleted) but the SETEVENTS command has not yet succeeded

    def _maybe_issue_command(self):
        """
        If there's at least one command queued and we're not currently
        processing a command, this will issue the next one on the
        wire.
        """
        if self.command:
            return

        if len(self.commands):
            self.command = self.commands.pop(0)
            (d, cmd, cmd_arg) = self.command
            self.defer = d

            self.debuglog.write(cmd + b'\n')
            self.debuglog.flush()

            data = cmd + b'\r\n'
            txtorlog.msg("cmd: {}".format(data.strip()))
            self.transport.write(data)

    def _auth_failed(self, fail):
        """
        Errback if authentication fails.
        """
        # it should be impossible for post_bootstrap to be
        # already-called/failed at this point; _auth_failed only stems
        # from _do_authentication failing
        self.post_bootstrap.errback(fail)
        return None

    def _safecookie_authchallenge(self, reply):
        """
        Callback on AUTHCHALLENGE SAFECOOKIE
        """
        if self._cookie_data is None:
            raise RuntimeError("Cookie data not read.")
        kw = parse_keywords(reply.replace(' ', '\n'))

        server_hash = base64.b16decode(kw['SERVERHASH'])
        server_nonce = base64.b16decode(kw['SERVERNONCE'])
        # FIXME put string in global. or something.
        expected_server_hash = hmac_sha256(
            b"Tor safe cookie authentication server-to-controller hash",
            self._cookie_data + self.client_nonce + server_nonce,
        )

        if not compare_via_hash(expected_server_hash, server_hash):
            raise RuntimeError(
                'Server hash not expected; wanted "%s" and got "%s".' %
                (base64.b16encode(expected_server_hash),
                 base64.b16encode(server_hash))
            )

        client_hash = hmac_sha256(
            b"Tor safe cookie authentication controller-to-server hash",
            self._cookie_data + self.client_nonce + server_nonce
        )
        client_hash_hex = base64.b16encode(client_hash)
        return self.queue_command(b'AUTHENTICATE ' + client_hash_hex)

    def _read_cookie(self, cookiefile):
        """
        Open and read a cookie file
        :param cookie: Path to the cookie file
        """
        self._cookie_data = None
        self._cookie_data = open(cookiefile, 'rb').read()
        if len(self._cookie_data) != 32:
            raise RuntimeError(
                "Expected authentication cookie to be 32 bytes, got %d" %
                len(self._cookie_data)
            )

    def _do_authenticate(self, protoinfo):
        """
        Callback on PROTOCOLINFO to actually authenticate once we know
        what's supported.
        """
        methods = None
        cookie_auth = False
        for line in protoinfo.split('\n'):
            if line[:5] == 'AUTH ':
                kw = parse_keywords(line[5:].replace(' ', '\n'))
                methods = kw['METHODS'].split(',')
        if not methods:
            raise RuntimeError(
                "Didn't find AUTH line in PROTOCOLINFO response."
            )

        if 'SAFECOOKIE' in methods or 'COOKIE' in methods:
            cookiefile_match = re.search(r'COOKIEFILE=("(?:[^"\\]|\\.)*")',
                                         protoinfo)
            if cookiefile_match:
                cookiefile = cookiefile_match.group(1)
                cookiefile = unescape_quoted_string(cookiefile)
                try:
                    self._read_cookie(cookiefile)
                    cookie_auth = True
                except IOError as why:
                    txtorlog.msg("Reading COOKIEFILE failed: " + str(why))
                    if self.password_function and 'HASHEDPASSWORD' in methods:
                        txtorlog.msg("Falling back to password")
                    else:
                        raise RuntimeError(
                            "Failed to read COOKIEFILE '{fname}': {msg}\n".format(
                                fname=cookiefile,
                                msg=str(why),
                            )
                            # "On Debian, join the debian-tor group"
                        )
            else:
                txtorlog.msg("Didn't get COOKIEFILE")
                raise RuntimeError(
                    "Got 'COOKIE' or 'SAFECOOKIE' method, but no 'COOKIEFILE'"
                )

        if cookie_auth:
            if 'SAFECOOKIE' in methods:
                txtorlog.msg("Using SAFECOOKIE authentication", cookiefile,
                             len(self._cookie_data), "bytes")
                self.client_nonce = os.urandom(32)

                cmd = b'AUTHCHALLENGE SAFECOOKIE ' + \
                      hexlify(self.client_nonce)
                d = self.queue_command(cmd)
                d.addCallback(self._safecookie_authchallenge)
                d.addCallback(self._bootstrap)
                return d

            elif 'COOKIE' in methods:
                txtorlog.msg("Using COOKIE authentication",
                             cookiefile, len(self._cookie_data), "bytes")
                d = self.authenticate(self._cookie_data)
                d.addCallback(self._bootstrap)
                return d

        if self.password_function and 'HASHEDPASSWORD' in methods:
            d = defer.maybeDeferred(self.password_function)
            d.addCallback(maybe_coroutine)
            d.addCallback(self._do_password_authentication)
            return d

        if 'NULL' in methods:
            d = self.queue_command('AUTHENTICATE')
            d.addCallback(self._bootstrap)
            return d

        return defer.fail(
            RuntimeError(
                "The Tor I connected to doesn't support SAFECOOKIE nor COOKIE"
                " authentication (or we can't read the cookie files) and I have"
                " no password_function specified."
            )
        )

    def _do_password_authentication(self, passwd):
        if not passwd:
            raise RuntimeError("No password available.")
        d = self.authenticate(passwd)
        d.addCallback(self._bootstrap)
        d.addErrback(self._auth_failed)

    def _set_valid_events(self, events):
        "used as a callback; see _bootstrap"
        self.valid_events = {}
        for x in events.split():
            self.valid_events[x] = Event(x)

    @defer.inlineCallbacks
    def _bootstrap(self, *args):
        """
        The inlineCallbacks decorator allows us to make this method
        look synchronous; see the Twisted docs. Each yeild is for a
        Deferred after which the method continues. When this method
        finally exits, we're set up and do the post_bootstrap
        callback.
        """

        try:
            self.valid_signals = yield self.get_info('signal/names')
            self.valid_signals = self.valid_signals['signal/names']
        except TorProtocolError:
            self.valid_signals = ["RELOAD", "DUMP", "DEBUG", "NEWNYM",
                                  "CLEARDNSCACHE"]

        self.version = yield self.get_info('version')
        self.version = self.version['version']
        txtorlog.msg("Connected to a Tor with VERSION", self.version)
        eventnames = yield self.get_info('events/names')
        eventnames = eventnames['events/names']
        self._set_valid_events(eventnames)

        yield self.queue_command('USEFEATURE EXTENDED_EVENTS')

        self.post_bootstrap.callback(self)
        defer.returnValue(self)

    # State Machine transitions and matchers. See the __init__ method
    # for a way to output a GraphViz dot diagram of the machine.

    def _is_end_line(self, line):
        "for FSM"
        return line.strip() == '.'

    def _is_not_end_line(self, line):
        "for FSM"
        return not self._is_end_line(line)

    def _is_single_line_response(self, line):
        "for FSM"
        try:
            code = int(line[:3])
        except Exception:
            return False

        sl = len(line) > 3 and line[3] == ' '
        # print "single line?",line,sl
        if sl:
            self.code = code
            return True
        return False

    def _start_command(self, line):
        "for FSM"
        # print "startCommand",self.code,line
        self.code = int(line[:3])
        # print "startCommand:",self.code
        if self.command and self.command[2] is not None:
            self.command[2](line[4:])
        else:
            self.response = line[4:] + '\n'
        return None

    def _is_continuation_line(self, line):
        "for FSM"
        code = int(line[:3])
        if self.code and self.code != code:
            raise RuntimeError("Unexpected code %d, wanted %d" % (code,
                                                                  self.code))
        return line[3] == '-'

    def _is_multi_line(self, line):
        "for FSM"
        code = int(line[:3])
        if self.code and self.code != code:
            raise RuntimeError("Unexpected code %d, wanted %d" % (code,
                                                                  self.code))
        return line[3] == '+'

    def _accumulate_multi_response(self, line):
        "for FSM"
        if self.command and self.command[2] is not None:
            self.command[2](line)

        else:
            self.response += (line + '\n')
        return None

    def _accumulate_response(self, line):
        "for FSM"
        if self.command and self.command[2] is not None:
            self.command[2](line[4:])

        else:
            self.response += (line[4:] + '\n')
        return None

    def _is_finish_line(self, line):
        "for FSM"
        # print "isFinish",line
        if len(line) < 1:
            return False
        if line[0] == '.':
            return True
        if len(line) > 3 and line[3] == ' ':
            return True
        return False

    def _broadcast_response(self, line):
        "for FSM"
        if len(line) > 3:
            if self.code >= 200 and self.code < 300 and \
               self.command and self.command[2] is not None:
                self.command[2](line[4:])
                resp = ''

            else:
                resp = self.response + line[4:]
        else:
            resp = self.response
        self.response = ''
        if self.code is None:
            raise RuntimeError("No code set yet in broadcast response.")
        elif self.code >= 200 and self.code < 300:
            if self.defer is None:
                raise RuntimeError(
                    'Got a response, but didn\'t issue a command: "%s"' % resp
                )
            if resp.endswith('\nOK'):
                resp = resp[:-3]
            self.defer.callback(resp)
        elif self.code >= 500 and self.code < 600:
            err = TorProtocolError(self.code, resp)
            self.defer.errback(err)
        elif self.code >= 600 and self.code < 700:
            self._handle_notify(self.code, resp)
            self.code = None
            return
        else:
            raise RuntimeError(
                "Unknown code in broadcast response %d." % self.code
            )

        # note: we don't do this for 600-level responses
        self.command = None
        self.code = None
        self.defer = None
        self._maybe_issue_command()
        return None
