# -*- coding: utf-8
# Database routines
# ******************
import os
import sys
import traceback
import warnings

from sqlalchemy import exc as sa_exc

from globaleaks import models, DATABASE_VERSION
from globaleaks.db.appdata import db_load_default_questionnaires, db_load_default_fields
from globaleaks.handlers.base import Session
from globaleaks.models import Config
from globaleaks.models.config_desc import ConfigFilters
from globaleaks.orm import transact, transact_sync, get_session, make_db_uri
from globaleaks.settings import Settings
from globaleaks.state import State, TenantState
from globaleaks.utils import security
from globaleaks.utils.objectdict import ObjectDict
from globaleaks.utils.utility import log

def get_db_file(db_path):
    path = os.path.join(db_path, 'globaleaks.db')
    if os.path.exists(path):
        session = get_session(make_db_uri(path))
        version_db = session.query(models.Config.value).filter(Config.tid == 1, Config.var_name == u'version_db').one()[0]
        session.close()
        return version_db, path

    for i in reversed(range(0, DATABASE_VERSION + 1)):
        file_name = 'glbackend-%d.db' % i
        db_file_path = os.path.join(db_path, 'db', file_name)
        if os.path.exists(db_file_path):
            return i, db_file_path

    return 0, ''


def create_db():
    from globaleaks.orm import get_engine
    from globaleaks.models import Base

    engine = get_engine()
    engine.execute('PRAGMA foreign_keys = ON')
    engine.execute('PRAGMA secure_delete = ON')
    engine.execute('PRAGMA auto_vacuum = FULL')

    Base.metadata.create_all(engine)


@transact_sync
def init_db(session):
    from globaleaks.handlers.admin import tenant
    tenant.db_create(session, {'label': 'root'})
    db_load_default_questionnaires(session)
    db_load_default_fields(session)


def update_db():
    """
    This function handles update of an existing database
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

            log.err('Performing schema migration from version %d to version %d', db_version, DATABASE_VERSION)

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
    returns a list the basenames of files tracked by InternalFile and ReceiverFile.
    """
    ifiles = [x[0] for x in session.query(models.InternalFile.filename)]
    rfiles = [x[0] for x in session.query(models.ReceiverFile.filename)]
    wbfiles = [x[0] for x in session.query(models.WhistleblowerFile.filename)]

    return [files for files in list(set(ifiles + rfiles + wbfiles))]


@transact_sync
def sync_clean_untracked_files(session):
    """
    removes files in Settings.attachments_path that are not
    tracked by InternalFile/ReceiverFile.
    """
    tracked_files = db_get_tracked_files(session)
    for filesystem_file in os.listdir(Settings.attachments_path):
        if filesystem_file not in tracked_files:
            file_to_remove = os.path.join(Settings.attachments_path, filesystem_file)
            try:
                log.debug('Removing untracked file: %s', file_to_remove)
                security.overwrite_and_remove(file_to_remove)
            except OSError:
                log.err('Failed to remove untracked file', file_to_remove)


def db_set_cache_exception_delivery_list(session, tenant_cache):
    """
    Constructs and sets a list of (email_addr, public_key) pairs that will receive
    errors from the platform. If the email_addr is empty, drop the tuple from the list.
    """
    lst = []

    if tenant_cache.enable_developers_exception_notification:
        lst.append((u'globaleaks-stackexception@lists.globaleaks.org', ''))

    if tenant_cache.enable_admin_exception_notification:
        results = session.query(models.User.mail_address, models.User.pgp_key_public).filter(models.User.role == u'admin')
        lst.extend([(mail, pub_key) for mail, pub_key in results])

    if Settings.developer_name:
        tenant_cache.notification.source_name = Settings.developer_name

    tenant_cache.notification.exception_delivery_list = filter(lambda x: x[0] != '', lst)


def db_refresh_tenant_cache(session, tid_list):
    """
    This routine loads in memory few variables of node and notification tables
    that are subject to high usage.
    """
    for cfg in session.query(Config).filter(Config.tid.in_(tid_list)):
        tenant_cache = State.tenant_cache[cfg.tid]

        if cfg.var_name in ConfigFilters['node']:
            tenant_cache[cfg.var_name] = cfg.get_v()
        elif cfg.var_name in ConfigFilters['notification']:
            tenant_cache.setdefault('notification', ObjectDict())
            tenant_cache['notification'][cfg.var_name] = cfg.get_v()

    for tid, lang in models.EnabledLanguage.tid_list(session, tid_list):
        State.tenant_cache[tid].setdefault('languages_enabled', []).append(lang)


def db_refresh_memory_variables(session, to_refresh=None):
    session.flush()

    tenant_map = {tenant.id:tenant for tenant in session.query(models.Tenant).filter(models.Tenant.active == True)}

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
            api_id = session.query(models.User.id).filter(models.User.tid == 1, models.User.role == u'admin').order_by(models.User.creation_date).first()
            if api_id is not None:
                State.api_token_session = Session(1, api_id, 'admin', 'enabled')

    rootdomain = State.tenant_cache[1].rootdomain
    root_onionservice = State.tenant_cache[1].onionservice

    for tid in to_refresh:
        if tid not in tenant_map:
            continue

        tenant = tenant_map[tid]
        hostnames = []
        onionnames = []
        if not tenant.active and tid != 1:
            continue

        if rootdomain != '':
            hostnames.append('p{}.{}'.format(tid, rootdomain).encode())

        if root_onionservice != '':
            onionnames.append('p{}.{}'.format(tid, root_onionservice).encode())

        if tenant.subdomain != '':
            if rootdomain != '':
                onionnames.append('{}.{}'.format(tenant.subdomain, rootdomain).encode())
            if root_onionservice != '':
                onionnames.append('{}.{}'.format(tenant.subdomain, root_onionservice).encode())

        if State.tenant_cache[tid].hostname != '':
            hostnames.append(State.tenant_cache[tid].hostname.encode())

        if State.tenant_cache[tid].onionservice != '':
            onionnames.append(State.tenant_cache[tid].onionservice.encode())

        State.tenant_cache[tid].hostnames = hostnames
        State.tenant_cache[tid].onionnames = onionnames

        State.tenant_hostname_id_map.update({h:tid for h in hostnames + onionnames})


@transact
def refresh_memory_variables(session, to_refresh=None):
    return db_refresh_memory_variables(session, to_refresh)


@transact_sync
def sync_refresh_memory_variables(session, to_refresh=None):
    return db_refresh_memory_variables(session, to_refresh)
