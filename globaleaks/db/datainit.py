# -*- coding: UTF-8
#   GLBackend Database
#   ******************
from __future__ import with_statement
import os

from globaleaks.rest import errors
from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks import models
from globaleaks.security import get_salt, hash_password
from globaleaks.utils.utility import datetime_now, datetime_null, acquire_url_address, log
from globaleaks.third_party import rstr
from globaleaks.models import Node, ApplicationData


def opportunistic_appdata_init():
    """
    Setup application data evaluating the presence of the following paths:
        - production data path: /usr/share/globaleaks/glclient/data/
        - development data paths: ../GLClient/app/data/
                                  ../../GLClient/app/data/
    """

    # Fields and applicative data initialization

    fields_l10n = [ "/usr/share/globaleaks/glclient/data/fields_l10n.json",
                    "../GLClient/app/data/fields_l10n.json",
                    "../../GLClient/app/data/fields_l10n.json"]

    appdata_dict = None

    for f710n in fields_l10n:

        if os.path.exists(f710n):

            with file(f710n, 'r') as f:
                import json
                json_string = f.read()
                appdata_dict = json.loads(json_string)
                return appdata_dict

    if not appdata_dict:
        print "Note: no app data init opportunity!"
        return dict({'version': 0, 'fields': []}) # empty!

    return appdata_dict


@transact
def initialize_node(store, results, only_node, templates, appdata):
    """
    TODO refactor with languages the email_template, develop a dedicated
    function outside the node, and inquire fucking YHWH about the
    callbacks existence/usage
    """
    node = models.Node(only_node)

    # by default, only english is the surely present language
    node.languages_enabled = GLSetting.defaults.languages_enabled

    node.receipt_salt = get_salt(rstr.xeger('[A-Za-z0-9]{56}'))

    node.wizard_done = GLSetting.skip_wizard

    node.creation_date = datetime_now()

    store.add(node)

    admin_salt = get_salt(rstr.xeger('[A-Za-z0-9]{56}'))
    admin_password = hash_password(u"globaleaks", admin_salt)

    admin_dict = {
        'username': u'admin',
        'password': admin_password,
        'salt': admin_salt,
        'role': u'admin',
        'state': u'enabled',
        }

    admin = models.User(admin_dict)

    admin.last_login = datetime_null()

    store.add(admin)

    notification = models.Notification()

    # our defaults for free, because we're like Gandhi of the mail accounts.
    notification.server = "mail.headstrong.de"
    notification.port = 587
    # port 587/SMTP-TLS or 465/SMTPS
    notification.username = "sendaccount@lists.globaleaks.org"
    notification.password = "sendaccount99"
    notification.security = "TLS"

    notification.source_name = "Default GlobaLeaks sender"
    notification.source_email = notification.username

    # Those fields are sets as default in order to show to the Admin the various
    # 'variables' used in the template.
    notification.encrypted_tip_template = { GLSetting.memory_copy.default_language:
                                            templates['encrypted_tip'] }
    notification.encrypted_tip_mail_title = { GLSetting.memory_copy.default_language:
                                              "[Tip %TipNum%] for %ReceiverName% in %ContextName%: new Tip (Encrypted)" }

    notification.plaintext_tip_template= { GLSetting.memory_copy.default_language:
                                           templates['plaintext_tip'] }
    notification.plaintext_tip_mail_title = { GLSetting.memory_copy.default_language:
                                              "[Tip %TipNum%] for %ReceiverName% in %ContextName%: new ClearText" }

    notification.encrypted_message_template = { GLSetting.memory_copy.default_language: templates['encrypted_message'] }
    notification.encrypted_message_mail_title = { GLSetting.memory_copy.default_language:
                                                  "[Tip %TipNum%] for %ReceiverName% in %ContextName%: New message (Encrypted)" }

    notification.plaintext_message_template = { GLSetting.memory_copy.default_language: templates['plaintext_message'] }
    notification.plaintext_message_mail_title = { GLSetting.memory_copy.default_language:
                                                  "[Tip %TipNum%] for %ReceiverName% in %ContextName%: New message" }

    notification.encrypted_file_template = { GLSetting.memory_copy.default_language: templates['encrypted_file'] }
    notification.encrypted_file_mail_title = { GLSetting.memory_copy.default_language:
                                               "[Tip %TipNum%] for %ReceiverName% in %ContextName%: File appended (Encrypted)" }

    notification.plaintext_file_template = { GLSetting.memory_copy.default_language: templates['plaintext_file'] }
    notification.plaintext_file_mail_title = { GLSetting.memory_copy.default_language:
                                               "[Tip %TipNum%] for %ReceiverName% in %ContextName%: File appended" }

    notification.encrypted_comment_template = { GLSetting.memory_copy.default_language: templates['encrypted_comment'] }
    notification.encrypted_comment_mail_title = { GLSetting.memory_copy.default_language:
                                                  "[Tip %TipNum%] for %ReceiverName% in %ContextName%: New comment (Encrypted)" }

    notification.plaintext_comment_template = { GLSetting.memory_copy.default_language: templates['plaintext_comment'] }
    notification.plaintext_comment_mail_title = { GLSetting.memory_copy.default_language:
                                                  "[Tip %TipNum%] for %ReceiverName% in %ContextName%: New comment" }

    notification.zip_description = { GLSetting.memory_copy.default_language:
                                     templates['zip_collection'] }

    store.add(notification)

    if appdata:
        log.debug("Development environment detected: Installing ApplicationData from file")

        new_appdata = ApplicationData()
        new_appdata.fields = appdata['fields']
        new_appdata.fields_version = appdata['version']

        store.add(new_appdata)
    else:
        log.debug("Not Development environment: waiting for Wizard setup ApplicationData")



@transact_ro
def import_memory_variables(store):
    """
    to get fast checks, import (same) of the Node variable in GLSetting,
    this function is called every time that Node is updated.
    """
    try:
        node = store.find(models.Node).one()

        GLSetting.memory_copy.maximum_filesize = node.maximum_filesize
        GLSetting.memory_copy.maximum_namesize = node.maximum_namesize
        GLSetting.memory_copy.maximum_textsize = node.maximum_textsize

        GLSetting.memory_copy.tor2web_admin = node.tor2web_admin
        GLSetting.memory_copy.tor2web_submission = node.tor2web_submission
        GLSetting.memory_copy.tor2web_receiver = node.tor2web_receiver
        GLSetting.memory_copy.tor2web_unauth = node.tor2web_unauth

        GLSetting.memory_copy.anomaly_checks = node.anomaly_checks
        GLSetting.memory_copy.allow_unencrypted = node.allow_unencrypted

        GLSetting.memory_copy.exception_email = node.exception_email
        GLSetting.memory_copy.default_language = node.default_language

        # Email settings are copyed because they are used when an exception raises
        # and we can't go to check in the DB, because that's shall be exception source
        notif = store.find(models.Notification).one()

        GLSetting.memory_copy.notif_server = notif.server
        GLSetting.memory_copy.notif_port = int(notif.port)
        GLSetting.memory_copy.notif_password = notif.password
        GLSetting.memory_copy.notif_username = notif.username
        GLSetting.memory_copy.notif_security = notif.security
        GLSetting.memory_copy.notif_source_name = notif.source_name
        GLSetting.memory_copy.notif_source_email = notif.source_email

    except Exception as e:
        raise errors.InvalidInputFormat("Cannot import memory variables: %s" % e)


@transact
def apply_cli_options(store):
    """
    Remind: GLSetting.unchecked_tor_input contain data that are not
    checked until this function!
    """

    node = store.find(Node).one()

    verb = "Hardwriting"
    accepted = {}
    if GLSetting.unchecked_tor_input.has_key('hostname_tor_content'):
        composed_hs_url = 'http://%s' % GLSetting.unchecked_tor_input['hostname_tor_content']
        composed_t2w_url = 'https://%s.to' % GLSetting.unchecked_tor_input['hostname_tor_content']

        if not acquire_url_address(composed_hs_url, hidden_service=True, http=True) or \
                not acquire_url_address(composed_t2w_url, hidden_service=False, http=True):
            print "[!!] Invalid content found in the 'hostname' file specified (%s): Ignored" % \
                  GLSetting.unchecked_tor_input['hostname_tor_content']
        else:
            accepted.update({ 'hidden_service' : unicode(composed_hs_url) })
            print "[+] %s hidden service in the DB: %s" % (verb, composed_hs_url)

            if node.public_site:
                print "[!!] Public Website (%s) is not automatically overwritten by (%s)" % \
                      (node.public_site, composed_t2w_url)
            else:
                accepted.update({ 'public_site' : unicode(composed_t2w_url) })
                print "[+] %s public site in the DB: %s" % (verb, composed_t2w_url)

            verb = "Overwritting"

    if GLSetting.cmdline_options.public_website:
        if not acquire_url_address(GLSetting.cmdline_options.public_website, hidden_service=False, http=True):
            print "[!!] Invalid public site: %s: Ignored" % GLSetting.cmdline_options.public_website
        else:
            print "[+] %s public site in the DB: %s" % (verb, GLSetting.cmdline_options.public_website)
            accepted.update({ 'public_site' : unicode(GLSetting.cmdline_options.public_website) })

    if GLSetting.cmdline_options.hidden_service:
        if not acquire_url_address(GLSetting.cmdline_options.hidden_service, hidden_service=True, http=True):
            print "[!!] Invalid hidden service: %s: Ignored" % GLSetting.cmdline_options.hidden_service
        else:
            print "[+] %s hidden service in the DB: %s" % (verb, GLSetting.cmdline_options.hidden_service)
            accepted.update({ 'hidden_service' : unicode(GLSetting.cmdline_options.hidden_service) })

    if accepted:
        node = store.find(Node).one()
        for k, v, in accepted.iteritems():
            setattr(node, k, v)
        store.commit()

    # return configured URL for the log/console output
    node = store.find(Node).one()
    if node.hidden_service or node.public_site:
        return [ node.hidden_service, node.public_site ]
    else:
        return None



