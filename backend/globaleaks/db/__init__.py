# -*- coding: utf-8
# Database routines
# ******************
import os
import sys
import traceback
from storm import exceptions

from globaleaks import models, security, DATABASE_VERSION, FIRST_DATABASE_VERSION_SUPPORTED
from globaleaks.handlers.base import Session
from globaleaks.models.config import Config
from globaleaks.orm import transact, transact_sync
from globaleaks.settings import Settings
from globaleaks.state import State
from globaleaks.utils.objectdict import ObjectDict
from globaleaks.utils.utility import log

XTIDX = 1


def get_db_file(db_path):
    for i in reversed(range(0, DATABASE_VERSION + 1)):
        file_name = 'glbackend-%d.db' % i
        db_file_path = os.path.join(db_path, file_name)
        if os.path.exists(db_file_path):
            return i, db_file_path

    return 0, ''


def db_create_tables(store):
    with open(Settings.db_schema) as f:
        create_queries = ''.join(f.readlines()).split(';')

    for create_query in create_queries:
        try:
            store.execute(create_query + ';')
        except exceptions.OperationalError as exc:
            log.err("OperationalError in [%s]", create_query)
            log.err(exc)


@transact_sync
def init_db(store):
    from globaleaks.handlers.admin import tenant

    log.debug("Performing database initialization...")

    db_create_tables(store)

    tenant.db_create(store, {})


def update_db():
    """
    This function handles update of an existing database
    """
    try:
        db_version, _ = get_db_file(Settings.db_path)
        if db_version == 0:
            return 0

        from globaleaks.db import migration

        log.err("Found an already initialized database version: %d", db_version)

        if FIRST_DATABASE_VERSION_SUPPORTED <= db_version < DATABASE_VERSION:
            log.err("Performing schema migration from version %d to version %d", db_version, DATABASE_VERSION)
            migration.perform_schema_migration(db_version)
            log.err("Migration completed with success!")

        else:
            log.err('Performing data update')
            # TODO on normal startup this line is run. We need better control flow here.
            migration.perform_data_update(os.path.abspath(os.path.join(Settings.db_path, 'glbackend-%d.db' % DATABASE_VERSION)))

    except Exception as exception:
        log.err("Migration failure: %s", exception)
        log.err("Verbose exception traceback:")
        etype, value, tback = sys.exc_info()
        log.info('\n'.join(traceback.format_exception(etype, value, tback)))
        return -1


def db_get_tracked_files(store):
    """
    returns a list the basenames of files tracked by InternalFile and ReceiverFile.
    """
    ifiles = list(store.find(models.InternalFile).values(models.InternalFile.file_path))
    rfiles = list(store.find(models.ReceiverFile).values(models.ReceiverFile.file_path))
    wbfiles = list(store.find(models.WhistleblowerFile).values(models.WhistleblowerFile.file_path))

    return [os.path.basename(files) for files in list(set(ifiles + rfiles + wbfiles))]


@transact_sync
def sync_clean_untracked_files(store):
    """
    removes files in Settings.submission_path that are not
    tracked by InternalFile/ReceiverFile.
    """
    tracked_files = db_get_tracked_files(store)
    for filesystem_file in os.listdir(Settings.submission_path):
        if filesystem_file not in tracked_files:
            file_to_remove = os.path.join(Settings.submission_path, filesystem_file)
            try:
                log.debug("Removing untracked file: %s", file_to_remove)
                security.overwrite_and_remove(file_to_remove)
            except OSError:
                log.err("Failed to remove untracked file", file_to_remove)


def db_get_exception_delivery_list(store, tid):
    """
    Constructs a list of (email_addr, public_key) pairs that will receive errors from the platform.
    If the email_addr is empty, drop the tuple from the list.
    """
    notif_fact = models.config.NotificationFactory(store, tid)

    lst = []

    if notif_fact.get_val(u'enable_developers_exception_notification'):
        lst.append((u'globaleaks-stackexception@lists.globaleaks.org', ''))

    if notif_fact.get_val(u'enable_admin_exception_notification'):
        results = store.find(models.User, models.User.role==u'admin') \
                      .values(models.User.mail_address, models.User.pgp_key_public)

        lst.extend([(mail, pub_key) for (mail, pub_key) in results])

    return filter(lambda x: x[0] != '', lst)


def db_refresh_tenant_cache(store, tid):
    """
    This routine loads in memory few variables of node and notification tables
    that are subject to high usage.
    """
    tenant_cache = ObjectDict(models.config.NodeFactory(store, tid).admin_export())

    tenant_cache.accept_tor2web_access = {
        'admin': tenant_cache.tor2web_admin,
        'custodian': tenant_cache.tor2web_custodian,
        'whistleblower': tenant_cache.tor2web_whistleblower,
        'receiver': tenant_cache.tor2web_receiver
    }

    tenant_cache.languages_enabled = models.l10n.EnabledLanguage.list(store, tid)

    tenant_cache.notif = ObjectDict(models.config.NotificationFactory(store, tid).admin_export())
    tenant_cache.notif.exception_delivery_list = db_get_exception_delivery_list(store, tid)
    if Settings.developer_name:
        tenant_cache.notif.source_name = Settings.developer_name

    tenant_cache.private = ObjectDict(models.config.PrivateFactory(store, tid).mem_copy_export())

    if tid == XTIDX and tenant_cache.private.admin_api_token_digest:
        api_id = store.find(models.User.id, models.User.tid==XTIDX, models.User.role==u'admin').order_by(models.User.creation_date).first()
        if api_id is not None:
            State.api_token_session = Session(1, api_id, 'admin', 'enabled')

    return tenant_cache


def db_refresh_memory_variables(store):
    tenant_cache = dict()
    tenant_hostname_id_map = dict()

    tenant_map = {tenant.id: tenant for tenant in store.find(models.Tenant)}
    for tenant in tenant_map.values():
        tenant_cache[tenant.id] = db_refresh_tenant_cache(store, tenant.id)

    # Update state object with changes coming from tenant
    root_hostname = tenant_cache[1].hostname
    for tid, tenant_cache_item in tenant_cache.items():
        tenant = tenant_map[tid]
        hostnames = []

        if not tenant.active and tid != 1:
            continue

        if root_hostname != "" and tenant.subdomain != "":
            hostnames.append('{}.{}'.format(tenant.subdomain, root_hostname))

        if root_hostname != "":
            hostnames.append('p{}.{}'.format(tid, root_hostname))

        if tenant_cache_item.hostname != "":
            hostnames.append(tenant_cache_item.hostname)

	if tenant_cache_item.onionservice != "":
	    hostnames.append(tenant_cache_item.onionservice)

        tenant_hostname_id_map.update({h : tid for h in hostnames})

    State.tenant_cache = tenant_cache
    State.tenant_hostname_id_map = tenant_hostname_id_map


@transact
def refresh_memory_variables(store):
    return db_refresh_memory_variables(store)


@transact_sync
def sync_refresh_memory_variables(store):
    return db_refresh_memory_variables(store)
