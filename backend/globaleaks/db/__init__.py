# -*- coding: UTF-8
# Database routines
# ******************
import os
import sys
import traceback

from cyclone.util import ObjectDict
from twisted.internet.defer import succeed, inlineCallbacks
from storm import exceptions
from storm.locals import Store, create_database

from globaleaks import models, __version__, DATABASE_VERSION
from globaleaks.db.appdata import db_update_appdata, db_fix_fields_attrs
from globaleaks.handlers.admin import files
from globaleaks.models import config, l10n
from globaleaks.models.config import NodeFactory, NotificationFactory, PrivateFactory
from globaleaks.models.l10n import EnabledLanguage
from globaleaks.orm import transact, transact_ro
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


@transact
def init_db(store, use_single_lang=False):
    db_create_tables(store)
    appdata_dict = db_update_appdata(store)

    log.debug("Performing database initialization...")

    config.system_cfg_init(store)

    if GLSettings.skip_wizard:
        NodeFactory(store).set_val('wizard_done', True)

    log.debug("Inserting internationalized strings...")

    if not use_single_lang:
        EnabledLanguage.add_all_supported_langs(store, appdata_dict)
    else:
        EnabledLanguage.add_new_lang(store, u'en', appdata_dict)

    with open(os.path.join(GLSettings.client_path, 'logo.png'), 'r') as logo_file:
        data = logo_file.read()
        files.db_add_file(store, data, u'logo')

    with open(os.path.join(GLSettings.client_path, 'favicon.ico'), 'r') as favicon_file:
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
            migration.perform_data_update(os.path.abspath(os.path.join(GLSettings.db_path, 'glbackend-%d.db' % DATABASE_VERSION)))

    return db_version


@transact_ro
def get_tracked_files(store):
    """
    returns a list the basenames of files tracked by InternalFile and ReceiverFile.
    """
    ifiles = list(store.find(models.InternalFile).values(models.InternalFile.file_path))
    rfiles = list(store.find(models.ReceiverFile).values(models.ReceiverFile.file_path))

    return [os.path.basename(files) for files in list(set(ifiles + rfiles))]


@inlineCallbacks
def clean_untracked_files():
    """
    removes files in GLSettings.submission_path that are not
    tracked by InternalFile/ReceiverFile.
    """
    tracked_files = yield get_tracked_files()
    for filesystem_file in os.listdir(GLSettings.submission_path):
        if filesystem_file not in tracked_files:
            file_to_remove = os.path.join(GLSettings.submission_path, filesystem_file)
            try:
                os.remove(file_to_remove)
            except OSError:
                log.err("Failed to remove untracked file" % file_to_remove)


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

    notif_ro = ObjectDict(NotificationFactory(store).admin_export())

    GLSettings.memory_copy.notif = notif_ro

    if GLSettings.developer_name:
        GLSettings.memory_copy.notif.source_name = GLSettings.developer_name

    if GLSettings.disable_mail_notification:
        GLSettings.memory_copy.notif.disable_admin_notification_emails = True
        GLSettings.memory_copy.notif.disable_custodian_notification_emails = True
        GLSettings.memory_copy.notif.disable_receiver_notification_emails = True

    GLSettings.memory_copy.private = ObjectDict(PrivateFactory(store).mem_copy_export())


@transact_ro
def refresh_memory_variables(*args):
    return db_refresh_memory_variables(*args)
