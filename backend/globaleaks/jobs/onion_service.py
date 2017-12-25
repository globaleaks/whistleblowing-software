# -*- coding: utf-8 -*-
# Implements configuration of Tor hidden service

import os
from txtorcon import build_local_tor_connection

from twisted.internet import reactor, defer

from globaleaks import models
from globaleaks.db import refresh_memory_variables
from globaleaks.rest.apicache import ApiCache
from globaleaks.jobs.base import BaseJob
from globaleaks.models.config import NodeFactory, PrivateFactory
from globaleaks.orm import transact
from globaleaks.utils.utility import log
from globaleaks.state import State


try:
    from txtorcon.torconfig import EphemeralHiddenService
except ImportError:
    from globaleaks.mocks.txtorcon_mocks import EphemeralHiddenService


__all__ = ['OnionService']


@transact
def list_onion_service_info(store):
    return [db_get_onion_service_info(store, tid)
        for tid in store.find(models.Tenant.id, active=True)]


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

    # Update external application state
    State.tenant_cache[tid].onionservice = hostname
    State.tenant_hostname_id_map[hostname] = tid


class OnionService(BaseJob):
    threaded = False
    print_startup_error = True
    tor_conn = None
    hs_map = {}
    startup_semaphore = dict()

    def operation(self):
        restart_deferred = defer.Deferred()

        control_socket = '/var/run/tor/control'

        def startup_callback(tor_conn):
            self.print_startup_error = True
            self.tor_conn = tor_conn
            self.tor_conn.protocol.on_disconnect = restart_deferred

            log.debug('Successfully connected to Tor control port')

            return self.add_all_hidden_services()

        def startup_errback(err):
            if self.print_startup_error:
                # Print error only on first run or failure or on a failure subsequent to a success condition
                self.print_startup_error = False
                log.err('Failed to initialize Tor connection; error: %s', err)

            restart_deferred.callback(None)

        if not os.path.exists(control_socket):
            startup_errback(Exception('Tor control port not open on %s; waiting for Tor to become available' % control_socket))
            return

        if not os.access(control_socket, os.R_OK):
            startup_errback(Exception('Unable to access %s; manual permission recheck needed' % control_socket))
            return

        d = build_local_tor_connection(reactor)
        d.addCallbacks(startup_callback, startup_errback)

        return restart_deferred

    def stop(self):
        super(OnionService, self).stop()

        if self.tor_conn is not None:
            tor_conn = self.tor_conn
            self.tor_conn = None
            return tor_conn.protocol.quit()

    @defer.inlineCallbacks
    def add_all_hidden_services(self):
        hostname_key_list = yield list_onion_service_info()

        if self.tor_conn is not None:
            for hostname, key, tid in hostname_key_list:
                if hostname not in self.hs_map:
                    yield self.add_hidden_service(hostname, key, tid)

    def add_hidden_service(self, hostname, key, tid):
        hs_loc = ('80 localhost:8083')
        if not hostname and not key:
            if tid in self.startup_semaphore:
                log.debug('Still waiting for hidden service to start', tid=tid)
                return self.startup_semaphore[tid]

            log.info('Creating new onion service', tid=tid)
            ephs = EphemeralHiddenService(hs_loc)
        else:
            log.info('Setting up existing onion service %s', hostname, tid=tid)
            ephs = EphemeralHiddenService(hs_loc, key)
            self.hs_map[hostname] = ephs

        @defer.inlineCallbacks
        def init_callback(ret):
            log.info('Initialization of hidden-service %s completed.', ephs.hostname, tid=tid)
            if not hostname and not key:
                del self.startup_semaphore[tid]

                if tid in State.tenant_cache:
                    self.hs_map[ephs.hostname] = ephs
                    yield set_onion_service_info(tid, ephs.hostname, ephs.private_key)
                else:
                    yield ephs.remove_from_tor(self.tor_conn.protocol)

                ApiCache().invalidate(tid)
                ApiCache().invalidate(1)

                yield refresh_memory_variables()

        def init_errback(failure):
            if tid in self.startup_semaphore:
                del self.startup_semaphore[tid]

            raise failure.value

        d = ephs.add_to_tor(self.tor_conn.protocol)

        # pylint: disable=no-member
        d.addCallbacks(init_callback, init_errback)
        # pylint: enable=no-member

        self.startup_semaphore[tid] = d

        return d

    @defer.inlineCallbacks
    def remove_unwanted_hidden_services(self):
        # Collect the list of all hidden services listed by tor then remove all of them
        # that are not present in the tenant cache ensuring that OnionService.hs_map is
        # kept up to date.
        running_services = yield self.get_all_hidden_services()

        tenant_services = {State.tenant_cache[tid].onionservice for tid in State.tenant_cache}

        for onion_addr in running_services:
            ephs = None
            if onion_addr not in tenant_services and onion_addr in self.hs_map:
                ephs = self.hs_map.pop(onion_addr)

            if ephs is not None:
                log.info('Removing onion address %s', ephs.hostname)
                yield ephs.remove_from_tor(self.tor_conn.protocol)

    @defer.inlineCallbacks
    def get_all_hidden_services(self):
        if self.tor_conn is None:
            defer.returnValue([])

        ret = yield self.tor_conn.protocol.get_info('onions/current')
        if ret == '':
            running_services = []
        else:
            x = ret.get('onions/current', '').strip().split('\n')
            running_services = [r+'.onion' for r in x]

        defer.returnValue(running_services)
