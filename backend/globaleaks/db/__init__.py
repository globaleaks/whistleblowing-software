# -*- coding: UTF-8
# Database routines
# ******************
import os
import re
import sys
import traceback

from storm import exceptions

from twisted.internet.defer import succeed, inlineCallbacks

from globaleaks import models,  __version__, DATABASE_VERSION
from globaleaks.db.appdata import db_init_appdata, load_default_fields
from globaleaks.handlers.admin.user import db_create_admin
from globaleaks.orm import transact, transact_ro
from globaleaks.rest import requests
from globaleaks.security import generateRandomSalt
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import log, datetime_null


def init_models():
    for model in models.model_list:
        model()
    return succeed(None)


def db_create_tables(store):
    if not os.access(GLSettings.db_schema, os.R_OK):
        log.err("Unable to access %s" % GLSettings.db_schema)
        raise Exception("Unable to access db schema file")

    with open(GLSettings.db_schema) as f:
        create_queries = ''.join(f.readlines()).split(';')
        for create_query in create_queries:
            try:
                store.execute(create_query + ';')
            except exceptions.OperationalError as exc:
                log.err("OperationalError in [%s]" % create_query)
                log.err(exc)

    init_models()
    # new is the only Models function executed without @transact, call .add, but
    # the called has to .commit and .close, operations commonly performed by decorator


@transact
def init_db(store):
    db_create_tables(store)
    appdata_dict = db_init_appdata(store)

    log.debug("Performing database initialization...")

    node = models.Node()
    node.wizard_done = GLSettings.skip_wizard
    node.receipt_salt = generateRandomSalt()

    for k in appdata_dict['node']:
        setattr(node, k, appdata_dict['node'][k])

    notification = models.Notification()
    for k in appdata_dict['templates']:
        setattr(notification, k, appdata_dict['templates'][k])

    store.add(node)
    store.add(notification)

    load_default_fields(store)

    admin_dict = {
        'username': u'admin',
        'password': u'globaleaks',
        'deeletable': False,
        'role': u'admin',
        'state': u'enabled',
        'deletable': False,
        'name': u'Admin',
        'description': u'',
        'mail_address': u'',
        'language': node.default_language,
        'timezone': node.default_timezone,
        'password_change_needed': False,
        'pgp_key_remove': False,
        'pgp_key_status': 'disabled',
        'pgp_key_info': '',
        'pgp_key_fingerprint': '',
        'pgp_key_public': '',
        'pgp_key_expiration': datetime_null()
    }

    admin = db_create_admin(store, admin_dict, node.default_language)
    admin.password_change_needed = False


def check_db_files():
    """
    This function checks the database version and executes eventually
    executes migration scripts
    """
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

    if len(db_files) == 1 and db_version > 0:
        from globaleaks.db import migration

        log.msg("Found an already initialized database version: %d" % db_version)

        if db_version < DATABASE_VERSION:
            log.msg("Performing update of database from version %d to version %d" % (db_version, DATABASE_VERSION))
            try:
                migration.perform_version_update(db_version)
                log.msg("Migration completed with success!")
            except Exception as exception:
                log.msg("Migration failure: %s" % exception)
                log.msg("Verbose exception traceback:")
                etype, value, tback = sys.exc_info()
                log.msg('\n'.join(traceback.format_exception(etype, value, tback)))
                return -1

    elif len(db_files) > 1:
        log.msg("Error: Cannot start the application because more than one database file are present in: %s" % GLSettings.db_path)
        log.msg("Manual check needed and is suggested to first make a backup of %s\n" % GLSettings.working_path)
        log.msg("Files found:")

        for f in db_files:
            log.msg("\t%s" % f)

        return -1

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
    node = store.find(models.Node).one()

    GLSettings.memory_copy.nodename = node.name

    GLSettings.memory_copy.maximum_filesize = node.maximum_filesize
    GLSettings.memory_copy.maximum_namesize = node.maximum_namesize
    GLSettings.memory_copy.maximum_textsize = node.maximum_textsize

    GLSettings.memory_copy.tor2web_access = {
        'admin': node.tor2web_admin,
        'custodian': node.tor2web_custodian,
        'whistleblower': node.tor2web_whistleblower,
        'receiver': node.tor2web_receiver,
        'unauth': node.tor2web_unauth
    }

    GLSettings.memory_copy.can_postpone_expiration = node.can_postpone_expiration
    GLSettings.memory_copy.can_delete_submission =  node.can_delete_submission
    GLSettings.memory_copy.can_grant_permissions = node.can_grant_permissions

    GLSettings.memory_copy.submission_minimum_delay = node.submission_minimum_delay
    GLSettings.memory_copy.submission_maximum_ttl =  node.submission_maximum_ttl

    GLSettings.memory_copy.allow_unencrypted = node.allow_unencrypted
    GLSettings.memory_copy.allow_iframes_inclusion = node.allow_iframes_inclusion

    GLSettings.memory_copy.enable_captcha = node.enable_captcha
    GLSettings.memory_copy.enable_proof_of_work = node.enable_proof_of_work

    GLSettings.memory_copy.default_language = node.default_language
    GLSettings.memory_copy.default_timezone = node.default_timezone
    GLSettings.memory_copy.languages_enabled  = node.languages_enabled

    GLSettings.memory_copy.receipt_salt  = node.receipt_salt

    GLSettings.memory_copy.simplified_login = node.simplified_login

    GLSettings.memory_copy.threshold_free_disk_megabytes_high = node.threshold_free_disk_megabytes_high
    GLSettings.memory_copy.threshold_free_disk_megabytes_medium = node.threshold_free_disk_megabytes_medium
    GLSettings.memory_copy.threshold_free_disk_megabytes_low = node.threshold_free_disk_megabytes_low

    GLSettings.memory_copy.threshold_free_disk_percentage_high = node.threshold_free_disk_percentage_high
    GLSettings.memory_copy.threshold_free_disk_percentage_medium = node.threshold_free_disk_percentage_medium
    GLSettings.memory_copy.threshold_free_disk_percentage_low = node.threshold_free_disk_percentage_low

    notif = store.find(models.Notification).one()

    GLSettings.memory_copy.notif_server = notif.server
    GLSettings.memory_copy.notif_port = notif.port
    GLSettings.memory_copy.notif_password = notif.password
    GLSettings.memory_copy.notif_username = notif.username
    GLSettings.memory_copy.notif_source_email = notif.source_email
    GLSettings.memory_copy.notif_security = notif.security
    GLSettings.memory_copy.tip_expiration_threshold = notif.tip_expiration_threshold
    GLSettings.memory_copy.notification_threshold_per_hour = notif.notification_threshold_per_hour
    GLSettings.memory_copy.notification_suspension_time = notif.notification_suspension_time

    if GLSettings.developer_name:
        GLSettings.memory_copy.notif_source_name = GLSettings.developer_name
    else:
        GLSettings.memory_copy.notif_source_name = notif.source_name

    GLSettings.memory_copy.notif_source_name = notif.source_name
    GLSettings.memory_copy.notif_source_email = notif.source_email

    GLSettings.memory_copy.exception_email_address = notif.exception_email_address
    GLSettings.memory_copy.exception_email_pgp_key_info = notif.exception_email_pgp_key_info
    GLSettings.memory_copy.exception_email_pgp_key_fingerprint = notif.exception_email_pgp_key_fingerprint
    GLSettings.memory_copy.exception_email_pgp_key_public = notif.exception_email_pgp_key_public
    GLSettings.memory_copy.exception_email_pgp_key_expiration = notif.exception_email_pgp_key_expiration
    GLSettings.memory_copy.exception_email_pgp_key_status = notif.exception_email_pgp_key_status

    if GLSettings.disable_mail_notification:
        GLSettings.memory_copy.disable_admin_notification_emails = True
        GLSettings.memory_copy.disable_custodian_notification_emails = True
        GLSettings.memory_copy.disable_receiver_notification_emails = True
    else:
        GLSettings.memory_copy.disable_admin_notification_emails = notif.disable_admin_notification_emails
        GLSettings.memory_copy.disable_admin_custodian_emails = notif.disable_custodian_notification_emails
        GLSettings.memory_copy.disable_receiver_notification_emails = notif.disable_receiver_notification_emails


@transact_ro
def refresh_memory_variables(*args):
    return db_refresh_memory_variables(*args)


@transact
def apply_cmdline_options(store):
    """
    Remind: GLSettings.unchecked_tor_input contain data that are not
    checked until this function!
    """
    node = store.find(models.Node).one()

    verb = "Hardwriting"
    if 'hostname_tor_content' in GLSettings.unchecked_tor_input:
        composed_hs_url = 'http://%s' % GLSettings.unchecked_tor_input['hostname_tor_content']
        hs = GLSettings.unchecked_tor_input['hostname_tor_content'].split('.onion')[0]
        composed_t2w_url = 'https://%s.tor2web.org' % hs

        if not (re.match(requests.hidden_service_regexp, composed_hs_url) or
                    re.match(requests.https_url_regexp, composed_t2w_url)):
            log.msg("[!!] Invalid content found in the 'hostname' file specified (%s): Ignored" % \
                    GLSettings.unchecked_tor_input['hostname_tor_content'])
        else:
            node.hidden_service = unicode(composed_hs_url)
            log.msg("[+] %s hidden service in the DB: %s" % (verb, composed_hs_url))

            if node.public_site:
                log.msg("[!!] Public Website (%s) is not automatically overwritten by (%s)" % \
                        (node.public_site, composed_t2w_url))
            else:
                node.public_site = unicode(composed_t2w_url)
                log_msg("[+] %s public site in the DB: %s" % (verb, composed_t2w_url))

            verb = "Overwriting"

    if GLSettings.cmdline_options.public_website:
        if not re.match(requests.https_url_regexp, GLSettings.cmdline_options.public_website):
            log.msg("[!!] Invalid public site: %s: Ignored" % GLSettings.cmdline_options.public_website)
        else:
            log.msg("[+] %s public site in the DB: %s" % (verb, GLSettings.cmdline_options.public_website))
            node.public_site = unicode(GLSettings.cmdline_options.public_website)

    if GLSettings.cmdline_options.hidden_service:
        if not re.match(requests.hidden_service_regexp, GLSettings.cmdline_options.hidden_service):
            log.msg("[!!] Invalid hidden service: %s: Ignored" % GLSettings.cmdline_options.hidden_service)
        else:
            log.msg("[+] %s hidden service in the DB: %s" % (verb, GLSettings.cmdline_options.hidden_service))
            node.hidden_service = unicode(GLSettings.cmdline_options.hidden_service)

    # return configured URL for the log/console output
    if node.hidden_service or node.public_site:
        GLSettings.configured_hosts = [node.hidden_service, node.public_site]


@transact
def update_version(store):
    node = store.find(models.Node).one()
    node.version = unicode(__version__)
    node.version_db = unicode(DATABASE_VERSION)
