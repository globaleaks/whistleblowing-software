# -*- coding: UTF-8
# GLBackend Database
# ******************
from __future__ import with_statement
import sys
import traceback

import os
from twisted.internet.defer import succeed, inlineCallbacks
from storm.exceptions import OperationalError
from globaleaks.utils.utility import log
from globaleaks.settings import transact, transact_ro, GLSettings
from globaleaks import models

from globaleaks.db.datainit import init_appdata, init_db, load_appdata


def init_models():
    for model in models.models_list:
        model()
    return succeed(None)


@transact
def create_tables_transaction(store):
    """
    @return: None, create the right table at the first start, and initialized
    the node.
    """
    if not os.access(GLSettings.db_schema_file, os.R_OK):
        log.err("Unable to access %s" % GLSettings.db_schema_file)
        raise Exception("Unable to access db schema file")

    with open(GLSettings.db_schema_file) as f:
        create_queries = ''.join(f.readlines()).split(';')
        for create_query in create_queries:
            try:
                store.execute(create_query + ';')
            except OperationalError as exc:
                log.err("OperationalError in [%s]" % create_query)
                log.err(exc)

    init_models()
    # new is the only Models function executed without @transact, call .add, but
    # the called has to .commit and .close, operations commonly performed by decorator


def create_tables(create_node=True):
    appdata_dict = load_appdata()

    db_exists = False
    if GLSettings.db_type == 'sqlite':
        db_path = GLSettings.db_uri.replace('sqlite:', '').split('?', 1)[0]
        if os.path.exists(db_path):
            db_exists = True

    if db_exists:
        ret = succeed(None)
        ret.addCallback(init_appdata, appdata_dict)
        return ret

    deferred = create_tables_transaction()
    deferred.addCallback(init_appdata, appdata_dict)

    if create_node:
        log.debug("Node initialization with defaults values")

        node_dict = {
            'name': u'',
            'description': dict({GLSettings.defaults.language: u''}),
            'presentation': dict({GLSettings.defaults.language: u''}),
            'footer': dict({GLSettings.defaults.language: u''}),
            'context_selector_label': dict({GLSettings.defaults.language: u''}),
            'security_awareness_title': dict({GLSettings.defaults.language: u''}),
            'security_awareness_text': dict({GLSettings.defaults.language: u''}),
            'whistleblowing_question': dict({GLSettings.defaults.language: u''}),
            'whistleblowing_button': dict({GLSettings.defaults.language: u''}),
            'hidden_service': u'',
            'public_site': u'',
            # advanced settings
            'maximum_filesize': GLSettings.defaults.maximum_filesize,
            'maximum_namesize': GLSettings.defaults.maximum_namesize,
            'maximum_textsize': GLSettings.defaults.maximum_textsize,
            'tor2web_admin': GLSettings.defaults.tor2web_access['admin'],
            'tor2web_custodian': GLSettings.defaults.tor2web_access['custodian'],
            'tor2web_whistleblower': GLSettings.defaults.tor2web_access['whistleblower'],
            'tor2web_receiver': GLSettings.defaults.tor2web_access['receiver'],
            'tor2web_unauth': GLSettings.defaults.tor2web_access['unauth'],
            'submission_minimum_delay' : GLSettings.defaults.submission_minimum_delay,
            'submission_maximum_ttl' : GLSettings.defaults.submission_maximum_ttl,
            'can_postpone_expiration': False,  # disabled by default
            'can_delete_submission': False,  # disabled too
            'ahmia': False,  # disabled too
            'allow_unencrypted': GLSettings.defaults.allow_unencrypted,
            'allow_iframes_inclusion': GLSettings.defaults.allow_iframes_inclusion,
            'languages_enabled': GLSettings.defaults.languages_enabled,
            'default_language': GLSettings.defaults.language,
            'default_timezone': GLSettings.defaults.timezone,
            'disable_privacy_badge': False,
            'disable_security_awareness_badge': False,
            'disable_security_awareness_questions': False,
            'simplified_login': True,
            'enable_custom_privacy_badge': False,
            'disable_key_code_hint': False,
            'custom_privacy_badge_tor': dict({GLSettings.defaults.language: u''}),
            'custom_privacy_badge_none': dict({GLSettings.defaults.language: u''}),
            'header_title_homepage': dict({GLSettings.defaults.language: u''}),
            'header_title_submissionpage': dict({GLSettings.defaults.language: u''}),
            'header_title_receiptpage': dict({GLSettings.defaults.language: u''}),
            'header_title_tippage': dict({GLSettings.defaults.language: u''}),
            'widget_comments_title': dict({GLSettings.defaults.language: u''}),
            'widget_messages_title': dict({GLSettings.defaults.language: u''}),
            'widget_files_title': dict({GLSettings.defaults.language: u''}),
            'landing_page': GLSettings.defaults.landing_page,
            'show_contexts_in_alphabetical_order': False,
            'threshold_free_disk_megabytes_high': 200,
            'threshold_free_disk_megabytes_medium': 500,
            'threshold_free_disk_megabytes_low': 1000,
            'threshold_free_disk_percentage_high': 3,
            'threshold_free_disk_percentage_medium': 5,
            'threshold_free_disk_percentage_low': 10
        }

        # Initialize the node and notification tables
        deferred.addCallback(init_db, node_dict, appdata_dict)

    return deferred


def check_db_files():
    """
    This function checks the database version and executes eventually
    executes migration scripts
    """
    db_version = -1
    for filename in os.listdir(GLSettings.gldb_path):
        if filename.startswith('glbackend'):
            if filename.endswith('.db'):
                nameindex = filename.rfind('glbackend')
                extensindex = filename.rfind('.db')
                fileversion = int(filename[nameindex + len('glbackend-'):extensindex])
                db_version = fileversion if fileversion > db_version else db_version
            elif filename.endswith('-journal'):
                # As left journals files can leak data undefinitely we
                # should manage to remove them.
                print "Found an undeleted DB journal file %s: deleting it." % single_file
                try:
                    os.unlink(os.path.join(dirpath, single_file))
                except Exception as excep:
                    print "Unable to remove %s: %s" % \
                        (os.unlink(os.path.join(dirpath, single_file)), excep)

    if db_version > -1:
        from globaleaks.db import migration

        print "Database version detected: %d" % db_version

        if db_version < GLSettings.db_version:
            print "Performing update of Database from version %d to version %d" % \
                  (db_version, GLSettings.db_version)
            try:
                migration.perform_version_update(db_version, GLSettings.db_version)
                print "GlobaLeaks database version %d: update complete!" % GLSettings.db_version
            except Exception:
                print "GlobaLeaks database version %d: update failure :(" % GLSettings.db_version
                print "Verbose exception traceback:"
                _, _, exc_traceback = sys.exc_info()
                traceback.print_tb(exc_traceback)
                quit(-1)


@transact_ro
def get_tracked_files(store):
    """
    returns a list the basenames of files tracked by InternalFile and ReceiverFile.
    """
    ifiles = list(store.find(models.InternalFile).values(models.InternalFile.file_path))
    rfiles = list(store.find(models.ReceiverFile).values(models.ReceiverFile.file_path))

    return [os.path.basename(files) for files in list(set(ifiles + rfiles))]


@inlineCallbacks
def clean_untracked_files(res):
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
