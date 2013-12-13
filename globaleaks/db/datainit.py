# -*- coding: UTF-8
#   GLBackend Database
#   ******************
from __future__ import with_statement

from globaleaks.rest import errors
from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks import models
from globaleaks.security import get_salt, hash_password
from globaleaks.utils.utility import datetime_now, datetime_null, acquire_url_address
from globaleaks.third_party import rstr
from globaleaks.models import Node


@transact
def initialize_node(store, results, only_node, templates):
    """
    TODO refactor with languages the email_template, develop a dedicated
    function outside the node, and inquire fucking YHWH about the
    callbacks existence/usage
    """
    from Crypto import Random
    Random.atfork()

    node = models.Node(only_node)

    # by default, only english is the surely present language
    node.languages_enabled = GLSetting.defaults.languages_enabled

    node.receipt_salt = get_salt(rstr.xeger('[A-Za-z0-9]{56}'))

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
        'failed_login_count': 0,
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
                                              "[%NodeName%][%TipUN%] Encrypted Tip" }
    notification.message_template = { GLSetting.memory_copy.default_language: templates['message'] }
    notification.message_mail_title = { GLSetting.memory_copy.default_language:
                                         "[%NodeName%][%TipUN%] New Message received" }
    notification.file_template = { GLSetting.memory_copy.default_language: templates['file'] }
    notification.file_mail_title = { GLSetting.memory_copy.default_language:
                                     "[%NodeName%][%TipUN%] New file added" }
    notification.comment_template = { GLSetting.memory_copy.default_language: templates['comment'] }
    notification.comment_mail_title = { GLSetting.memory_copy.default_language:
                                        "[%NodeName%][%TipUN%] New comment added" }
    notification.plaintext_tip_template= { GLSetting.memory_copy.default_language:
                                           templates['plaintext_tip'] }
    notification.plaintext_tip_mail_title = { GLSetting.memory_copy.default_language:
                                              "[%NodeName%][%TipUN%] Plaintext Tip" }

    notification.zip_description = { GLSetting.memory_copy.default_language:
                                     templates['zip_collection'] }

    store.add(notification)


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

        GLSetting.memory_copy.exception_email = node.exception_email
        GLSetting.memory_copy.default_language = node.default_language

        # Email settings are copyed because they are used when
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

    accepted = {}
    if GLSetting.cmdline_options.public_website:
        if not acquire_url_address(GLSetting.cmdline_options.public_website, hidden_service=False, http=True):
            print "[!!] Invalid public site: %s: Ignored" % GLSetting.cmdline_options.public_website
        else:
            print "[+] Hardwriting tor2web in DB:", GLSetting.cmdline_options.public_website
            accepted.update({ 'public_site' : unicode(GLSetting.cmdline_options.public_website) })

    if GLSetting.cmdline_options.hidden_service:
        if not acquire_url_address(GLSetting.cmdline_options.hidden_service, hidden_service=True, http=True):
            print "[!!] Invalid hidden service: %s: Ignored" % GLSetting.cmdline_options.hidden_service
        else:
            print "[+] Hardwriting hidden service in DB:", GLSetting.cmdline_options.hidden_service
            accepted.update({ 'hidden_service' : unicode(GLSetting.cmdline_options.hidden_service) })

    if accepted:
        node = store.find(Node).one()
        for k, v, in accepted.iteritems():
            setattr(node, k, v)


