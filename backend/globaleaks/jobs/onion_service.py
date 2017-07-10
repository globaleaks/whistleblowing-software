#        -*- encoding: utf-8 -*-
# Implements periodic checks in order to verify pgp key status and other consistencies:

from datetime import timedelta

from globaleaks import models
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.admin.user import db_get_admin_users
from globaleaks.handlers.user import user_serialize_user
from globaleaks.jobs.base import ServiceJob
from globaleaks.orm import transact
from globaleaks.settings import GLSettings
from globaleaks.utils.templating import Templating
from globaleaks.utils.utility import datetime_now, datetime_null

import txtorcon
from txtorcon import build_local_tor_connection
from twisted.internet import reactor
from twisted.internet.error import ConnectionRefusedError
from twisted.internet.defer import inlineCallbacks, Deferred
from twisted.python.filepath import FilePath

from globaleaks.models.config import NodeFactory, PrivateFactory
from globaleaks.rest.apicache import GLApiCache
from globaleaks.utils.utility import deferred_sleep, log

try:
   from txtorcon.torconfig import EphemeralHiddenService
except ImportError:
   from globaleaks.mocks.txtorcon_mocks import EphemeralHiddenService


__all__ = ['OnionService']


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


class OnionService(ServiceJob):
    name = "OnionService"
    threaded = False

    @inlineCallbacks
    def service(self, restart_deferred):
        hostname, key = yield get_onion_service_info()

        control_socket = FilePath('/var/run/tor/control')

        log.info('Waiting for Tor to become available')
        while not control_socket.exists():
            yield deferred_sleep(1)

        log.info('Starting up Tor connection')
        try:
            d = build_local_tor_connection(reactor)

            def errback(err):
                log.err('Failed to initialize Tor connection; Tor daemon is down or misconfigured . . .')
                restart_deferred.callback(None)
                raise err

            d.addErrback(errback)

            tor_conn = yield d

            tor_conn.protocol.on_disconnect = restart_deferred
        except ConnectionRefusedError as e:
            return

        log.debug('Successfully connected to Tor control port')

        hs_loc = ('80 localhost:8082')
        if hostname == '' and key == '':
            log.info('Creating new onion service')
            ephs = EphemeralHiddenService(hs_loc)
        else:
            log.info('Setting up existing onion service %s', hostname)
            ephs = EphemeralHiddenService(hs_loc, key)

        @inlineCallbacks
        def initialization_callback(ret):
            log.info('Initialization of hidden-service %s completed.', ephs.hostname)
            if hostname == '' and key == '':
                yield set_onion_service_info(ephs.hostname, ephs.private_key)

    def operation(self):
        deferred = Deferred()

        self.service(deferred)

        return deferred
