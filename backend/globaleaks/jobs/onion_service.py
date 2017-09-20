#        -*- encoding: utf-8 -*-
# Implements configuration of Tor hidden service

import os
from txtorcon import build_local_tor_connection

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, Deferred
from twisted.internet.error import ConnectionLost

from globaleaks.db import refresh_memory_variables
from globaleaks.jobs.base import BaseJob
from globaleaks.models.config import NodeFactory, PrivateFactory
from globaleaks.orm import transact
from globaleaks.rest.apicache import GLApiCache
from globaleaks.utils.utility import log


try:
    from txtorcon.torconfig import EphemeralHiddenService
except ImportError:
    from globaleaks.mocks.txtorcon_mocks import EphemeralHiddenService


__all__ = ['OnionService']


@transact
def get_onion_service_info(store):
    node_fact = NodeFactory(store)
    hostname = node_fact.get_val(u'onionservice')

    priv_fact = PrivateFactory(store)
    key = priv_fact.get_val(u'tor_onion_key')

    return hostname, key


@transact
def set_onion_service_info(store, hostname, key):
    node_fact = NodeFactory(store)
    node_fact.set_val(u'onionservice', hostname)

    priv_fact = PrivateFactory(store)
    priv_fact.set_val(u'tor_onion_key', key)

    GLApiCache.invalidate()


class OnionService(BaseJob):
    name = "OnionService"
    threaded = False
    print_startup_error = True
    tor_conn = None

    @inlineCallbacks
    def service(self, restart_deferred):
        hostname, key = yield get_onion_service_info()

        control_socket = '/var/run/tor/control'

        def startup_callback(tor_conn):
            self.print_startup_error = True
            self.tor_conn = tor_conn
            self.tor_conn.protocol.on_disconnect = restart_deferred

            log.debug('Successfully connected to Tor control port')

            hs_loc = ('80 localhost:8083')
            if not hostname and not key:
                log.info('Creating new onion service')
                ephs = EphemeralHiddenService(hs_loc)
            else:
                log.info('Setting up existing onion service %s', hostname)
                ephs = EphemeralHiddenService(hs_loc, key)

            @inlineCallbacks
            def initialization_callback(ret):
                log.info('Initialization of hidden-service %s completed.', ephs.hostname)
                if not hostname and not key:
                    yield set_onion_service_info(ephs.hostname, ephs.private_key)
                    yield refresh_memory_variables()

            d = ephs.add_to_tor(self.tor_conn.protocol)
            d.addCallback(initialization_callback) # pylint: disable=no-member

        def startup_errback(err):
            if self.print_startup_error:
                # Print error only on first run or failure or on a failure subsequent to a success condition
                self.print_startup_error = False
                log.err('Failed to initialize Tor connection; error: %s', err)

            restart_deferred.callback(None)

        if not os.path.exists(control_socket):
            startup_errback(Exception('Tor control port not open on /var/run/tor/control; waiting for Tor to become available'))
            return

        if not os.access(control_socket, os.R_OK):
            startup_errback(Exception('Unable to access /var/run/tor/control; manual permission recheck needed'))
            return

        d = build_local_tor_connection(reactor)
        d.addCallback(startup_callback)
        d.addErrback(startup_errback)

    def operation(self):
        deferred = Deferred()

        self.service(deferred)

        return deferred

    @inlineCallbacks
    def stop(self):
        if self.tor_conn is not None:
            yield self.tor_conn.protocol.quit()
            self.tor_conn = None

        yield super(OnionService, self).stop()
