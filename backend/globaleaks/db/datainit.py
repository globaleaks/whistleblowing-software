# -*- coding: UTF-8
#   GLBackend Database
#   ******************
from __future__ import with_statement

import json
import re
import os

from globaleaks.rest import errors, requests
from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks import models
from globaleaks.security import get_salt, hash_password
from globaleaks.utils.utility import datetime_now, datetime_null, log
from globaleaks.third_party import rstr
from globaleaks.models import Node, ApplicationData

def load_appdata():
    """
    Setup application data evaluating the presence of the following paths:
        - production data path: /usr/share/globaleaks/glclient/data/
        - development data paths: ../client/build/data/
                                  ../client/app/data/
    """

    # Fields and applicative data initialization

    fields_l10n = [ "/usr/share/globaleaks/glclient/data/appdata_l10n.json",
                    "../../../client/build/data/appdata_l10n.json",
                    "../../../client/app/data/appdata_l10n.json"]

    appdata_dict = None

    this_directory = os.path.dirname(__file__)

    for fl10n in fields_l10n:
        fl10n_file = os.path.join(this_directory, fl10n)

        if os.path.exists(fl10n_file):

            with file(fl10n_file, 'r') as f:
                json_string = f.read()
                appdata_dict = json.loads(json_string)
                return appdata_dict

    if not appdata_dict:
        print "No client (appdata_l10n.json) file found in fixed paths!"
        return dict({'version': 1, 'fields': []}) # empty!

    return appdata_dict


@transact
def init_appdata(store, result, appdata_dict):
    # Drop old appdata
    store.find(models.ApplicationData).remove()

    # Initialize the default data table evry time with
    # fresh data and fresh translations
    appdata = models.ApplicationData()
    appdata.fields = appdata_dict['fields']
    appdata.version = appdata_dict['version']
    store.add(appdata)


@transact
def init_db(store, result, node_dict, appdata_dict):
    """
    TODO refactor with languages the email_template, develop a dedicated
    function outside the node, and inquire fucking YHWH about the
    callbacks existence/usage
    """

    node = models.Node(node_dict)

    for k in appdata_dict['node']:
        setattr(node, k, appdata_dict['node'][k])

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
        'language': u"en",
        'timezone': 0,
        'password_change_needed': False,
    }

    admin = models.User(admin_dict)

    admin.last_login = datetime_null()
    admin.password_change_date = datetime_null()

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

    for k in appdata_dict['templates']:
        setattr(notification, k, appdata_dict['templates'][k])

    store.add(notification)

def db_import_memory_variables(store):
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

        GLSetting.memory_copy.allow_unencrypted = node.allow_unencrypted
        GLSetting.memory_copy.allow_iframes_inclusion = node.allow_iframes_inclusion

        GLSetting.memory_copy.exception_email = node.exception_email
        GLSetting.memory_copy.language = node.default_language
        GLSetting.memory_copy.default_timezone = node.default_timezone

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
        GLSetting.memory_copy.receiver_notif_enable = not notif.disable_receivers_notification_emails
        GLSetting.memory_copy.admin_notif_enable = not notif.disable_admin_notification_emails


    except Exception as e:
        raise errors.InvalidInputFormat("Cannot import memory variables: %s" % e)

@transact_ro
def import_memory_variables(*args):
    return db_import_memory_variables(*args)

@transact
def apply_cli_options(store):
    """
    Remind: GLSetting.unchecked_tor_input contain data that are not
    checked until this function!
    """

    node = store.find(Node).one()

    verb = "Hardwriting"
    accepted = {}
    if 'hostname_tor_content' in GLSetting.unchecked_tor_input:
        composed_hs_url = 'http://%s' % GLSetting.unchecked_tor_input['hostname_tor_content']
        hs = GLSetting.unchecked_tor_input['hostname_tor_content'].split('.onion')[0]
        composed_t2w_url = 'https://%s.tor2web.org' % hs

        if not (re.match(requests.hidden_service_regexp, composed_hs_url) or \
                re.match(requests.https_url_regexp, composed_t2w_url)):
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

            verb = "Overwriting"

    if GLSetting.cmdline_options.public_website:
        if not re.match(requests.https_url_regexp, GLSetting.cmdline_options.public_website):
            print "[!!] Invalid public site: %s: Ignored" % GLSetting.cmdline_options.public_website
        else:
            print "[+] %s public site in the DB: %s" % (verb, GLSetting.cmdline_options.public_website)
            accepted.update({ 'public_site' : unicode(GLSetting.cmdline_options.public_website) })

    if GLSetting.cmdline_options.hidden_service:
        if not re.match(requests.hidden_service_regexp, GLSetting.cmdline_options.hidden_service):
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
