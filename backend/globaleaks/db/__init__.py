# -*- coding: UTF-8
# Database routines
# ******************
import os
import sys
import traceback

from cyclone.util import ObjectDict
from storm import exceptions
from twisted.internet.defer import inlineCallbacks

from globaleaks import models, security, DATABASE_VERSION
from globaleaks.db.appdata import db_update_appdata, db_fix_fields_attrs
from globaleaks.handlers.admin import files
from globaleaks.models import config, l10n, User
from globaleaks.models.config import NodeFactory, NotificationFactory, PrivateFactory
from globaleaks.models.l10n import EnabledLanguage
from globaleaks.orm import transact, transact_sync
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import log


def db_create_tables(store):
    with open(GLSettings.db_schema) as f:
        create_queries = ''.join(f.readlines()).split(';')
        for create_query in create_queries:
            try:
                store.execute(create_query + ';')
            except exceptions.OperationalError as exc:
                log.err("OperationalError in [%s]" % create_query)
                log.err(exc)


@transact_sync
def init_db(store, use_single_lang=False):
    db_create_tables(store)
    appdata_dict = db_update_appdata(store)

    log.debug("Performing database initialization...")

    config.system_cfg_init(store)

    if not use_single_lang:
        EnabledLanguage.add_all_supported_langs(store, appdata_dict)
    else:
        EnabledLanguage.add_new_lang(store, u'en', appdata_dict)

    with open(os.path.join(GLSettings.client_path, 'data/logo.png'), 'r') as logo_file:
        data = logo_file.read()
        files.db_add_file(store, data, u'logo')

    with open(os.path.join(GLSettings.client_path, 'data/favicon.ico'), 'r') as favicon_file:
        data = favicon_file.read()
        files.db_add_file(store, data, u'favicon')


def perform_system_update():
    """
    This function checks the system and database versions and executes migration
    routines based on the system's state. After this function has completed the
    node is either ready for initialization (0), running a version of the DB
    (>1), or broken (-1).
    """
    from globaleaks.db import migration
    db_files = []
    max_version = 0
    min_version = 0
    for filename in os.listdir(GLSettings.db_path):
        if filename.startswith('glbackend'):
            filepath = os.path.join(GLSettings.db_path, filename)
            if filename.endswith('.db'):
                db_files.append(filepath)
                nameindex = filename.rfind('glbackend')
                extensindex = filename.rfind('.db')
                fileversion = int(filename[nameindex + len('glbackend-'):extensindex])
                max_version = fileversion if fileversion > max_version else max_version
                min_version = fileversion if fileversion < min_version else min_version

    db_version = max_version

    if len(db_files) > 1:
        log.msg("Error: Cannot start the application because more than one database file are present in: %s" % GLSettings.db_path)
        log.msg("Manual check needed and is suggested to first make a backup of %s\n" % GLSettings.working_path)
        log.msg("Files found:")

        for f in db_files:
            log.msg("\t%s" % f)

        return -1

    if len(db_files) == 1:
        log.msg("Found an already initialized database version: %d" % db_version)

        if db_version < DATABASE_VERSION:
            log.msg("Performing schema migration from version %d to version %d" % (db_version, DATABASE_VERSION))
            try:
                migration.perform_schema_migration(db_version)
            except Exception as exception:
                log.msg("Migration failure: %s" % exception)
                log.msg("Verbose exception traceback:")
                etype, value, tback = sys.exc_info()
                log.msg('\n'.join(traceback.format_exception(etype, value, tback)))
                return -1

            log.msg("Migration completed with success!")

        else:
            log.msg('Performing data update')
            # TODO on normal startup this line is run. We need better control flow here.
            migration.perform_data_update(os.path.abspath(os.path.join(GLSettings.db_path, 'glbackend-%d.db' % DATABASE_VERSION)))

    return db_version


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
    removes files in GLSettings.submission_path that are not
    tracked by InternalFile/ReceiverFile.
    """
    tracked_files = db_get_tracked_files(store)
    for filesystem_file in os.listdir(GLSettings.submission_path):
        if filesystem_file not in tracked_files:
            file_to_remove = os.path.join(GLSettings.submission_path, filesystem_file)
            try:
                log.debug("Removing untracked file: %s" % file_to_remove)
                security.overwrite_and_remove(file_to_remove)
            except OSError:
                log.err("Failed to remove untracked file" % file_to_remove)


def db_refresh_exception_delivery_list(store):
    """
    Constructs a list of (email_addr, public_key) pairs that will receive errors from the platform.
    If the email_addr is empty, drop the tuple from the list.
    """
    notif_fact = NotificationFactory(store)
    error_addr = notif_fact.get_val('exception_email_address')
    error_pk = notif_fact.get_val('exception_email_pgp_key_public')

    lst = [(error_addr, error_pk)]

    results = store.find(User, User.role==unicode('admin')) \
                   .values(User.mail_address, User.pgp_key_public)

    lst.extend([(mail, pub_key) for (mail, pub_key) in results])
    trimmed = filter(lambda x: x[0] != '', lst)
    GLSettings.memory_copy.notif.exception_delivery_list = trimmed


def db_refresh_memory_variables(store):
    """
    This routine loads in memory few variables of node and notification tables
    that are subject to high usage.
    """
    node_ro = ObjectDict(NodeFactory(store).admin_export())

    GLSettings.memory_copy = node_ro

    GLSettings.memory_copy.accept_tor2web_access = {
        'admin': node_ro.tor2web_admin,
        'custodian': node_ro.tor2web_custodian,
        'whistleblower': node_ro.tor2web_whistleblower,
        'receiver': node_ro.tor2web_receiver,
        'unauth': node_ro.tor2web_unauth
    }

    enabled_langs = models.l10n.EnabledLanguage.list(store)
    GLSettings.memory_copy.languages_enabled = enabled_langs

    notif_fact = NotificationFactory(store)
    notif_ro = ObjectDict(notif_fact.admin_export())

    GLSettings.memory_copy.notif = notif_ro

    if GLSettings.developer_name:
        GLSettings.memory_copy.notif.source_name = GLSettings.developer_name

    db_refresh_exception_delivery_list(store)

    GLSettings.memory_copy.private = ObjectDict(PrivateFactory(store).mem_copy_export())


@transact
def refresh_memory_variables(*args):
    return db_refresh_memory_variables(*args)

@transact_sync
def sync_refresh_memory_variables(*args):
    return db_refresh_memory_variables(*args)
