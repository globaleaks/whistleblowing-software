#        -*- coding: utf-8 -*-
# Implements configuration of Tor hidden service

import os
from txtorcon import build_local_tor_connection

from twisted.internet import reactor, defer

from globaleaks import models
from globaleaks.db import refresh_memory_variables
from globaleaks.jobs.base import BaseJob
from globaleaks.models.config import NodeFactory, PrivateFactory
from globaleaks.orm import transact
from globaleaks.rest.apicache import ApiCache
from globaleaks.utils.utility import log
from globaleaks.state import State

XTIDX = 1


try:
    from txtorcon.torconfig import EphemeralHiddenService
except ImportError:
    from globaleaks.mocks.txtorcon_mocks import EphemeralHiddenService


__all__ = ['OnionService']


@transact
def list_onion_service_info(store):
    return [db_get_onion_service_info(store, tid)
        for tid in store.find(models.Tenant.id, models.Tenant.active == True)]


@transact
def get_onion_service_info(store, tid):
    return db_get_onion_service_info(store, tid)


def db_get_onion_service_info(store, tid):
    node_fact = NodeFactory(store, tid)
    hostname = node_fact.get_val(u'onionservice')

    key = PrivateFactory(store, tid).get_val(u'tor_onion_key')

    return hostname, key, tid


@transact
def set_onion_service_info(store, tid, hostname, key):
    NodeFactory(store, tid).set_val(u'onionservice', hostname)
    PrivateFactory(store, tid).set_val(u'tor_onion_key', key)

    State.tenant_cache[tid].onionservice = hostname

    ApiCache.invalidate()


class OnionService(BaseJob):
    name = "OnionService"
    threaded = False
    print_startup_error = True
    tor_conn = None

    @defer.inlineCallbacks
    def service(self, restart_deferred):
        hostname_key_list = yield list_onion_service_info()

        control_socket = '/var/run/tor/control'

        def startup_callback(tor_conn):
            self.print_startup_error = True
            self.tor_conn = tor_conn
            self.tor_conn.protocol.on_disconnect = restart_deferred

            log.debug('Successfully connected to Tor control port')

            hs_loc = ('80 localhost:8083')
            for hostname, key, tid in hostname_key_list:
                if not hostname and not key:
                    log.info('Creating new onion service')
                    ephs = EphemeralHiddenService(hs_loc)
                else:
                    log.info('Setting up existing onion service %s', hostname)
                    ephs = EphemeralHiddenService(hs_loc, key)

                @defer.inlineCallbacks
                def initialization_callback(ret):
                    log.info('Initialization of hidden-service %s completed.', ephs.hostname)
                    if not hostname and not key:
                        yield set_onion_service_info(tid, ephs.hostname, ephs.private_key)
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
        deferred = defer.Deferred()

        self.service(deferred)

        return deferred

    def stop(self):
        super(OnionService, self).stop()

        if self.tor_conn is not None:
            tor_conn = self.tor_conn
            self.tor_conn = None
            return tor_conn.protocol.quit()
        else:
            return defer.succeed(None)
