# -*- coding: UTF-8
# Database routines
# ******************
import os
import re
import sys
import traceback

from storm import exceptions

from twisted.internet.defer import succeed, inlineCallbacks
from twisted.internet.threads import deferToThreadPool

from globaleaks import models
from globaleaks.db.appdata import db_init_appdata, load_default_fields
from globaleaks.handlers.admin.user import db_create_admin
from globaleaks.orm import transact, transact_ro
from globaleaks.rest import errors, requests
from globaleaks.security import get_salt
from globaleaks.settings import GLSettings
from globaleaks.third_party import rstr
from globaleaks.utils.utility import log, datetime_null


def init_models():
    for model in models.models_list:
        model()
    return succeed(None)


def db_create_tables(store):
    """
    """
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
    """
    """
    db_create_tables(store)
    appdata_dict = db_init_appdata(store)

    log.debug("Performing database initialization...")

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

    node = models.Node(node_dict)
    node.languages_enabled = GLSettings.defaults.languages_enabled
    node.receipt_salt = get_salt(rstr.xeger('[A-Za-z0-9]{56}'))
    node.wizard_done = GLSettings.skip_wizard

    for k in appdata_dict['node']:
        setattr(node, k, appdata_dict['node'][k])

    store.add(node)

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
        'language': GLSettings.defaults.language,
        'timezone': GLSettings.defaults.timezone,
        'password_change_needed': False,
        'pgp_key_status': 'disabled',
        'pgp_key_info': '',
        'pgp_key_fingerprint': '',
        'pgp_key_public': '',
        'pgp_key_expiration': datetime_null()
    }

    admin = db_create_admin(store, admin_dict, GLSettings.defaults.language)
    admin.password_change_needed = False

    submission_counter_dict = {
      'key': u'submission_sequence',
      'count': 0
    }

    store.add(models.Counter(submission_counter_dict))

    notification = models.Notification()
    for k in appdata_dict['templates']:
        setattr(notification, k, appdata_dict['templates'][k])

    load_default_fields(store)

    store.add(notification)


def check_db_files():
    """
    This function checks the database version and executes eventually
    executes migration scripts
    """
    db_version = 0
    for filename in os.listdir(GLSettings.db_path):
        if filename.startswith('glbackend'):
            if filename.endswith('.db'):
                nameindex = filename.rfind('glbackend')
                extensindex = filename.rfind('.db')
                fileversion = int(filename[nameindex + len('glbackend-'):extensindex])
                db_version = fileversion if fileversion > db_version else db_version
            elif filename.endswith('-journal'):
                # As left journals files can leak data undefinitely we
                # should manage to remove them.
                print "Found an undeleted DB journal file %s: deleting it." % filename
                filepath = os.path.join(GLSettings.db_path, filename)
                try:
                    os.unlink(filepath)
                except Exception as excep:
                    print "Unable to remove %s: %s" %(os.unlink(filepath), excep)

    if db_version > 0:
        from globaleaks.db import migration

        print "Found an already initialized database version: %d" % db_version

        if db_version < GLSettings.db_version:
            print "Performing update of database from version %d to version %d" % \
                  (db_version, GLSettings.db_version)
            try:
                migration.perform_version_update(db_version)
                print "Migration completed with success!"
            except Exception:
                print "Migration failure :("
                print "Verbose exception traceback:"
                _, _, exc_traceback = sys.exc_info()
                traceback.print_tb(exc_traceback)
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
    try:
        node = store.find(models.Node).one()

        GLSettings.memory_copy.maximum_filesize = node.maximum_filesize
        GLSettings.memory_copy.maximum_namesize = node.maximum_namesize
        GLSettings.memory_copy.maximum_textsize = node.maximum_textsize

        GLSettings.memory_copy.tor2web_access['admin'] = node.tor2web_admin
        GLSettings.memory_copy.tor2web_access['custodian'] = node.tor2web_custodian
        GLSettings.memory_copy.tor2web_access['whistleblower'] = node.tor2web_whistleblower
        GLSettings.memory_copy.tor2web_access['receiver'] = node.tor2web_receiver
        GLSettings.memory_copy.tor2web_access['unauth'] = node.tor2web_unauth

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
        GLSettings.memory_copy.notif_uses_tor = notif.torify

        GLSettings.memory_copy.exception_email_address = notif.exception_email_address
        GLSettings.memory_copy.exception_email_pgp_key_info = notif.exception_email_pgp_key_info
        GLSettings.memory_copy.exception_email_pgp_key_fingerprint = notif.exception_email_pgp_key_fingerprint
        GLSettings.memory_copy.exception_email_pgp_key_public = notif.exception_email_pgp_key_public
        GLSettings.memory_copy.exception_email_pgp_key_expiration = notif.exception_email_pgp_key_expiration
        GLSettings.memory_copy.exception_email_pgp_key_status = notif.exception_email_pgp_key_status

        if GLSettings.disable_mail_notification:
            GLSettings.memory_copy.disable_receiver_notification_emails = True
            GLSettings.memory_copy.disable_admin_notification_emails = True
        else:
            GLSettings.memory_copy.disable_receiver_notification_emails = notif.disable_receivers_notification_emails
            GLSettings.memory_copy.disable_admin_notification_emails = notif.disable_admin_notification_emails

    except Exception as e:
        raise errors.InvalidInputFormat("Cannot import memory variables: %s" % e)


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
    accepted = {}
    if 'hostname_tor_content' in GLSettings.unchecked_tor_input:
        composed_hs_url = 'http://%s' % GLSettings.unchecked_tor_input['hostname_tor_content']
        hs = GLSettings.unchecked_tor_input['hostname_tor_content'].split('.onion')[0]
        composed_t2w_url = 'https://%s.tor2web.org' % hs

        if not (re.match(requests.hidden_service_regexp, composed_hs_url) or
                    re.match(requests.https_url_regexp, composed_t2w_url)):
            print "[!!] Invalid content found in the 'hostname' file specified (%s): Ignored" % \
                  GLSettings.unchecked_tor_input['hostname_tor_content']
        else:
            accepted.update({'hidden_service': unicode(composed_hs_url)})
            print "[+] %s hidden service in the DB: %s" % (verb, composed_hs_url)

            if node.public_site:
                print "[!!] Public Website (%s) is not automatically overwritten by (%s)" % \
                      (node.public_site, composed_t2w_url)
            else:
                accepted.update({'public_site': unicode(composed_t2w_url)})
                print "[+] %s public site in the DB: %s" % (verb, composed_t2w_url)

            verb = "Overwriting"

    if GLSettings.cmdline_options.public_website:
        if not re.match(requests.https_url_regexp, GLSettings.cmdline_options.public_website):
            print "[!!] Invalid public site: %s: Ignored" % GLSettings.cmdline_options.public_website
        else:
            print "[+] %s public site in the DB: %s" % (verb, GLSettings.cmdline_options.public_website)
            accepted.update({'public_site': unicode(GLSettings.cmdline_options.public_website)})

    if GLSettings.cmdline_options.hidden_service:
        if not re.match(requests.hidden_service_regexp, GLSettings.cmdline_options.hidden_service):
            print "[!!] Invalid hidden service: %s: Ignored" % GLSettings.cmdline_options.hidden_service
        else:
            print "[+] %s hidden service in the DB: %s" % (verb, GLSettings.cmdline_options.hidden_service)
            accepted.update({'hidden_service': unicode(GLSettings.cmdline_options.hidden_service)})

    if accepted:
        node = store.find(models.Node).one()
        for k, v, in accepted.iteritems():
            setattr(node, k, v)

    # return configured URL for the log/console output
    if node.hidden_service or node.public_site:
        return [node.hidden_service, node.public_site]
    else:
        return None
