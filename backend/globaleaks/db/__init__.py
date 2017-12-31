# -*- coding: utf-8
# Database routines
# ******************
import os
import sys
import time
import traceback
from storm import exceptions
from storm.expr import In, Or
from globaleaks import models, security, DATABASE_VERSION, FIRST_DATABASE_VERSION_SUPPORTED
from globaleaks.handlers.base import Session
from globaleaks.models.config import Config, NodeFactory, PrivateFactory, NotificationFactory
from globaleaks.models.config_desc import ConfigFilters
from globaleaks.orm import transact, transact_sync
from globaleaks.settings import Settings
from globaleaks.state import State, TenantState
from globaleaks.utils.objectdict import ObjectDict
from globaleaks.utils.utility import log

def get_db_file(db_path):
    for i in reversed(range(0, DATABASE_VERSION + 1)):
        file_name = 'glbackend-%d.db' % i
        db_file_path = os.path.join(db_path, file_name)
        if os.path.exists(db_file_path):
            return (i, db_file_path)

    return (0, '')


def db_create_tables(store):
    with open(Settings.db_schema) as f:
        create_queries = ''.join(f.readlines()).split(';')
    for create_query in create_queries:
        try:
            store.execute(create_query + ';')
        except exceptions.OperationalError as exc:
            log.err('OperationalError in [%s]', create_query)
            log.err(exc)


@transact_sync
def init_db(store):
    from globaleaks.handlers.admin import tenant
    db_create_tables(store)
    tenant.db_create(store, {})


def update_db():
    """
    This function handles update of an existing database
    """
    db_version, _ = get_db_file(Settings.db_path)
    if db_version == 0:
        return 0

    log.err('Found an already initialized database version: %d', db_version)
    if db_version == DATABASE_VERSION:
        return DATABASE_VERSION

    log.err('Performing schema migration from version %d to version %d', db_version, DATABASE_VERSION)

    try:
        from globaleaks.db import migration
        migration.perform_migration(db_version)
    except Exception as exception:
        log.err('Migration failure: %s', exception)
        log.err('Verbose exception traceback:')
        etype, value, tback = sys.exc_info()
        log.info('\n'.join(traceback.format_exception(etype, value, tback)))
        return -1

    log.err('Migration completed with success!')

    return DATABASE_VERSION


def db_get_tracked_files(store):
    """
    returns a list the basenames of files tracked by InternalFile and ReceiverFile.
    """
    ifiles = list(store.find(models.InternalFile).values(models.InternalFile.file_path))
    rfiles = list(store.find(models.ReceiverFile).values(models.ReceiverFile.file_path))
    wbfiles = list(store.find(models.WhistleblowerFile).values(models.WhistleblowerFile.file_path))
    return [ os.path.basename(files) for files in list(set(ifiles + rfiles + wbfiles)) ]


@transact_sync
def sync_clean_untracked_files(store):
    """
    removes files in Settings.attachments_path that are not
    tracked by InternalFile/ReceiverFile.
    """
    tracked_files = db_get_tracked_files(store)
    for filesystem_file in os.listdir(Settings.attachments_path):
        if filesystem_file not in tracked_files:
            file_to_remove = os.path.join(Settings.attachments_path, filesystem_file)
            try:
                log.debug('Removing untracked file: %s', file_to_remove)
                security.overwrite_and_remove(file_to_remove)
            except OSError:
                log.err('Failed to remove untracked file', file_to_remove)


def db_set_cache_exception_delivery_list(store, tenant_cache):
    """
    Constructs and sets a list of (email_addr, public_key) pairs that will receive
    errors from the platform. If the email_addr is empty, drop the tuple from the list.
    """
    lst = []

    if tenant_cache.notification.enable_developers_exception_notification:
        lst.append((u'globaleaks-stackexception@lists.globaleaks.org', ''))

    if tenant_cache.notification.enable_admin_exception_notification:
        results = store.find(models.User, models.User.role == u'admin').values(models.User.mail_address, models.User.pgp_key_public)
        lst.extend([ (mail, pub_key) for mail, pub_key in results ])

    if Settings.developer_name:
        tenant_cache.notification.source_name = Settings.developer_name

    tenant_cache.notification.exception_delivery_list = filter(lambda x: x[0] != '', lst)


def db_refresh_tenant_cache(store, tid_list):
    """
    This routine loads in memory few variables of node and notification tables
    that are subject to high usage.
    """
    result_set = store.find(Config, In(Config.tid, tid_list)).order_by(Config.tid, Config.var_name)

    for cfg in result_set:
        tenant_cache = State.tenant_cache[cfg.tid]

        if cfg.var_name in ConfigFilters['node']:
            tenant_cache[cfg.var_name] = cfg.get_v()
        elif cfg.var_name in ConfigFilters['notification']:
            tenant_cache.setdefault('notification', ObjectDict())
            tenant_cache['notification'][cfg.var_name] = cfg.get_v()
        elif cfg.var_name in ConfigFilters['private']:
            tenant_cache.setdefault('private', ObjectDict())
            tenant_cache['private'][cfg.var_name] = cfg.get_v()

    for tid, lang in models.l10n.EnabledLanguage.tid_list(store, tid_list):
        State.tenant_cache[tid].setdefault('languages_enabled', []).append(lang)


def db_refresh_memory_variables(store, to_refresh=None):
    tenant_map = {tenant.id:tenant for tenant in store.find(models.Tenant, active=True)}

    existing_tids = set(tenant_map.keys())
    cached_tids = set(State.tenant_state.keys())

    to_remove = cached_tids - existing_tids
    to_add = existing_tids - cached_tids

    for tid in to_remove:
        del State.tenant_state[tid]
        del State.tenant_cache[tid]

    for tid in to_add:
        State.tenant_state[tid] = TenantState(State.settings)
        State.tenant_cache[tid] = ObjectDict()

    to_refresh = State.tenant_cache.keys() if to_refresh is None else to_refresh

    db_refresh_tenant_cache(store, to_refresh)
    if 1 in to_refresh:
        to_refresh = State.tenant_cache.keys()
        db_set_cache_exception_delivery_list(store, State.tenant_cache[1])

        if State.tenant_cache[1].private.admin_api_token_digest:
            api_id = store.find(models.User.id, models.User.tid == 1, models.User.role == u'admin').order_by(models.User.creation_date).first()
            if api_id is not None:
                State.api_token_session = Session(1, api_id, 'admin', 'enabled')

    root_hostname = State.tenant_cache[1].hostname
    root_onionservice = State.tenant_cache[1].onionservice

    for tid in to_refresh:
        if tid not in tenant_map:
            continue

        tenant = tenant_map[tid]
        hostnames = []
        onionnames = []
        if not tenant.active and tid != 1:
            continue

        if root_hostname != '':
            hostnames.append('p{}.{}'.format(tid, root_hostname))

        if root_onionservice != '':
            onionnames.append('p{}.{}'.format(tid, root_onionservice))

        if tenant.subdomain != '':
            if root_hostname != '':
                onionnames.append('{}.{}'.format(tenant.subdomain, root_hostname))
            if root_onionservice != '':
                onionnames.append('{}.{}'.format(tenant.subdomain, root_onionservice))

        if State.tenant_cache[tid].hostname != '':
            hostnames.append(State.tenant_cache[tid].hostname)

        if State.tenant_cache[tid].onionservice != '':
            onionnames.append(State.tenant_cache[tid].onionservice)

        State.tenant_cache[tid].hostnames = hostnames
        State.tenant_cache[tid].onionnames = onionnames

        State.tenant_hostname_id_map.update({h:tid for h in hostnames + onionnames})


@transact
def refresh_memory_variables(store, to_refresh=None):
    return db_refresh_memory_variables(store, to_refresh)


@transact_sync
def sync_refresh_memory_variables(store, to_refresh=None):
    return db_refresh_memory_variables(store, to_refresh)
