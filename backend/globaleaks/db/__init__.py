# -*- coding: utf-8
import os
import sys
import traceback
import warnings

from sqlalchemy import exc as sa_exc

from globaleaks import models, DATABASE_VERSION
from globaleaks.db.appdata import db_update_defaults
from globaleaks.handlers.admin.https import load_tls_dict_list
from globaleaks.models import Base, Config
from globaleaks.models.config_desc import ConfigFilters
from globaleaks.orm import get_engine, get_session, make_db_uri, transact, transact_sync
from globaleaks.sessions import Session
from globaleaks.settings import Settings
from globaleaks.state import State, TenantState
from globaleaks.utils import fs
from globaleaks.utils.log import log
from globaleaks.utils.objectdict import ObjectDict


def get_db_file(db_path):
    """
    Utility function to retrieve the database file path
    :param db_path: The path where to look for the database file
    :return: The version and the path of the existing database file
    """
    path = os.path.join(db_path, 'globaleaks.db')
    if os.path.exists(path):
        session = get_session(make_db_uri(path))
        version_db = session.query(models.Config.value).filter(Config.tid == 1, Config.var_name == 'version_db').one()[0]
        session.close()
        return version_db, path

    for i in reversed(range(0, DATABASE_VERSION + 1)):
        file_name = 'glbackend-%d.db' % i
        db_file_path = os.path.join(db_path, 'db', file_name)
        if os.path.exists(db_file_path):
            return i, db_file_path

    return 0, ''


def create_db():
    """
    Utility function to create a new database
    """
    engine = get_engine()
    engine.execute('PRAGMA foreign_keys = ON')
    engine.execute('PRAGMA secure_delete = ON')
    engine.execute('PRAGMA auto_vacuum = FULL')

    Base.metadata.create_all(engine)


@transact_sync
def init_db(session):
    """
    Transaction for initializing the application database
    :param session: An ORM session
    """
    from globaleaks.handlers.admin import tenant
    tenant.db_create(session, {'mode': 'default', 'label': 'root'})
    db_update_defaults(session)


def update_db():
    """
    This function handles the update of an existing database
    :return: The database version
    """
    db_version, db_file_path = get_db_file(Settings.working_path)
    if db_version == 0:
        return 0

    try:
        with warnings.catch_warnings():
            from globaleaks.db import migration
            warnings.simplefilter("ignore", category=sa_exc.SAWarning)

            log.err('Found an already initialized database version: %d', db_version)
            if db_version == DATABASE_VERSION:
                migration.perform_data_update(db_file_path)
                return DATABASE_VERSION

            log.err('Performing schema migration from version %d to version %d',
                    db_version, DATABASE_VERSION)

            migration.perform_migration(db_version)

    except Exception as exception:
        log.err('Migration failure: %s', exception)
        log.err('Verbose exception traceback:')
        etype, value, tback = sys.exc_info()
        log.info('\n'.join(traceback.format_exception(etype, value, tback)))
        return -1

    log.err('Migration completed with success!')

    return DATABASE_VERSION


def db_get_tracked_files(session):
    """
    Transaction for retrieving the list of attachment files tracked by the application database
    :param session: An ORM session
    :return: The list of filenames of the attachment files
    """
    ifiles = list(session.query(models.InternalFile.filename).distinct())
    rfiles = list(session.query(models.ReceiverFile.filename).distinct())
    wbfiles = list(session.query(models.WhistleblowerFile.filename).distinct())

    return [x[0] for x in ifiles + rfiles + wbfiles]


@transact_sync
def sync_clean_untracked_files(session):
    """
    Transaction for removing files that are not tracked by the application database
    :param session: An ORM session
    """
    tracked_files = db_get_tracked_files(session)
    for filesystem_file in os.listdir(Settings.attachments_path):
        if filesystem_file not in tracked_files:
            file_to_remove = os.path.join(Settings.attachments_path, filesystem_file)
            log.debug('Removing untracked file: %s', file_to_remove)
            try:
                fs.overwrite_and_remove(file_to_remove)
            except OSError:
                log.err('Failed to remove untracked file', file_to_remove)


@transact_sync
def sync_initialize_snimap(session):
    """
    Transaction for loading TLS certificates and initialize the SNI map
    :param session: An ORM session
    """
    for cfg in load_tls_dict_list(session):
        if cfg['https_enabled']:
            State.snimap.load(cfg['tid'], cfg)


def db_set_cache_exception_delivery_list(session, tenant_cache):
    """
    Constructs and sets a list of (email_addr, public_key) pairs
    that will receive errors from the platform.
    """
    tenant_cache.notification.exception_delivery_list = []

    if not Settings.devel_mode and tenant_cache.enable_developers_exception_notification:
        tenant_cache.notification.exception_delivery_list.append(('globaleaks-stackexception@lists.globaleaks.org', ''))

    if tenant_cache.enable_admin_exception_notification:
        results = session.query(models.User.mail_address, models.User.pgp_key_public) \
                         .filter(models.User.tid == 1, models.User.state == 'enabled', models.User.role == 'admin')
        tenant_cache.notification.exception_delivery_list.extend([(mail, pub_key) for mail, pub_key in results])


def db_refresh_tenant_cache(session, tid_list):
    """
    This routine loads in memory few variables of node and notification tables
    that are subject to high usage.
    """
    for cfg in session.query(Config).filter(Config.tid.in_(tid_list)):
        tenant_cache = State.tenant_cache[cfg.tid]

        if cfg.var_name in ConfigFilters['node']:
            tenant_cache[cfg.var_name] = cfg.value
        elif cfg.var_name in ConfigFilters['notification']:
            tenant_cache.setdefault('notification', ObjectDict())
            tenant_cache['notification'][cfg.var_name] = cfg.value

    for tid, lang in models.EnabledLanguage.tid_list(session, tid_list):
        State.tenant_cache[tid].setdefault('languages_enabled', []).append(lang)

    for tid in tid_list:
        State.tenant_cache[tid]['ip_filter'] = {}
        State.tenant_cache[tid]['https_allowed'] = {}
        State.tenant_cache[tid]['redirects'] = {}

        for x in [('admin', 'ip_filter_admin_enable', 'ip_filter_admin'),
                  ('custodian', 'ip_filter_custodian_enable', 'ip_filter_custodian'),
                  ('receiver', 'ip_filter_receiver_enable', 'ip_filter_receiver'),
                  ('whistleblower', 'ip_filter_whistleblower_enable', 'ip_filter_whistleblower')]:
            if State.tenant_cache[tid].get(x[1], False) and State.tenant_cache[1][x[2]]:
                State.tenant_cache[tid]['ip_filter'][x[0]] = State.tenant_cache[1][x[2]]

        for x in ['admin', 'custodian', 'receiver', 'whistleblower']:
            State.tenant_cache[tid]['https_allowed'][x] = State.tenant_cache[tid].get('https_' + x, True)

        if State.tenant_cache[tid].mode == 'whistleblowing.it':
            State.tenant_cache[tid]['https_preload'] = State.tenant_cache[1]['https_preload']
            State.tenant_cache[tid]['frame_ancestors'] = State.tenant_cache[1]['frame_ancestors']

    for redirect in session.query(models.Redirect).filter(models.Redirect.tid.in_(tid_list)):
        State.tenant_cache[tid]['redirects'][redirect.path1] = redirect.path2


def db_refresh_memory_variables(session, to_refresh=None):
    tenant_map = {tenant.id: tenant for tenant in session.query(models.Tenant).filter(models.Tenant.active.is_(True))}

    existing_tids = set(tenant_map.keys())
    cached_tids = set(State.tenant_state.keys())

    to_remove = cached_tids - existing_tids
    to_add = existing_tids - cached_tids

    for tid in to_remove:
        if tid in State.tenant_state:
            del State.tenant_state[tid]

        if tid in State.tenant_cache:
            del State.tenant_cache[tid]

    for tid in to_add:
        State.tenant_state[tid] = TenantState(State)
        State.tenant_cache[tid] = ObjectDict()

    if to_refresh is None:
        to_refresh = tenant_map.keys()
    else:
        to_refresh = [tid for tid in to_refresh if tid in tenant_map]

    if to_refresh:
        db_refresh_tenant_cache(session, to_refresh)

    if 1 in to_refresh:
        to_refresh = State.tenant_cache.keys()
        db_set_cache_exception_delivery_list(session, State.tenant_cache[1])

        if State.tenant_cache[1].admin_api_token_digest:
            State.api_token_session = Session(1, 0, 1, 'admin', False, False, '', '')

        log.setloglevel(State.tenant_cache[1].log_level)

    rootdomain = State.tenant_cache[1].rootdomain
    root_onionservice = State.tenant_cache[1].onionservice

    for tid in to_refresh:
        if tid not in tenant_map:
            continue

        tenant = tenant_map[tid]
        if not tenant.active and tid != 1:
            continue

        hostnames = []
        onionnames = []

        if State.tenant_cache[tid].hostname != '':
            hostnames.append(State.tenant_cache[tid].hostname.encode())

        if State.tenant_cache[tid].onionservice != '':
            onionnames.append(State.tenant_cache[tid].onionservice.encode())

        if tenant.subdomain != '':
            if rootdomain != '':
                onionnames.append('{}.{}'.format(tenant.subdomain, rootdomain).encode())
            if root_onionservice != '':
                onionnames.append('{}.{}'.format(tenant.subdomain, root_onionservice).encode())

        State.tenant_cache[tid].hostnames = hostnames
        State.tenant_cache[tid].onionnames = onionnames

        State.tenant_hostname_id_map.update({h: tid for h in hostnames + onionnames})


@transact
def refresh_memory_variables(session, to_refresh=None):
    return db_refresh_memory_variables(session, to_refresh)


@transact_sync
def sync_refresh_memory_variables(session, to_refresh=None):
    return db_refresh_memory_variables(session, to_refresh)
