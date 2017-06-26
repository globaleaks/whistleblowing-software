# -*- coding: utf-8 -*-
import txtorcon
from txtorcon import build_local_tor_connection
from twisted.internet import reactor
from twisted.internet.error import ConnectionRefusedError
from twisted.internet.defer import inlineCallbacks, Deferred

from globaleaks.orm import transact
from globaleaks.models.config import NodeFactory, PrivateFactory
from globaleaks.rest.apicache import GLApiCache
from globaleaks.utils.utility import log

try:
   from txtorcon.torconfig import EphemeralHiddenService
except ImportError:
   from globaleaks.mocks.txtorcon_mocks import EphemeralHiddenService


@transact
def get_onion_service_info(store):
    node_fact = NodeFactory(store)
    hostname = node_fact.get_val('onionservice')

    priv_fact = PrivateFactory(store)
    key = priv_fact.get_val('tor_onion_key')

    return hostname, key


@transact
def set_onion_service_info(store, hostname, key):
    node_fact = NodeFactory(store)
    node_fact.set_val('onionservice', hostname)

    priv_fact = PrivateFactory(store)
    priv_fact.set_val('tor_onion_key', key)


@inlineCallbacks
def configure_tor_hs(bind_port):
    hostname, key = yield get_onion_service_info()

    log.info('Starting up Tor connection')
    try:
        tor_conn = yield build_local_tor_connection(reactor)
        tor_conn.protocol.on_disconnect = Deferred()
    except ConnectionRefusedError as e:
        log.err('Tor daemon is down or misconfigured . . . starting up anyway')
        return
    log.debug('Successfully connected to Tor control port')

    hs_loc = ('80 localhost:%d' % bind_port)
    if hostname == '':
        log.info('Creating new onion service')
        ephs = EphemeralHiddenService(hs_loc)
    else:
        log.info('Setting up existing onion service %s', hostname)
        ephs = EphemeralHiddenService(hs_loc, key)

    @inlineCallbacks
    def shutdown_callback():
        log.info('Shutting down Tor onion service %s' % ephs.hostname)
        if not getattr(tor_conn.protocol.on_disconnect, 'called', True):
            log.debug('Removing onion service')
            yield ephs.remove_from_tor(tor_conn.protocol)
        log.debug('Successfully handled Tor cleanup')

    @inlineCallbacks
    def initialization_callback(ret):
        log.info('Initialization of hidden-service %s completed.' % (ephs.hostname))
        if hasattr(ephs, 'private_key'):
            yield set_onion_service_info(ephs.hostname, ephs.private_key)

        reactor.addSystemEventTrigger('before', 'shutdown', shutdown_callback)

    d = ephs.add_to_tor(tor_conn.protocol)
    d.addCallback(initialization_callback) # pylint: disable=no-member
