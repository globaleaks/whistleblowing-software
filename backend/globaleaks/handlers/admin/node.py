# -*- coding: UTF-8
#
#   /admin/node
#   *****
# Implementation of the code executed on handler /admin/node
#
import os

from twisted.internet.defer import inlineCallbacks

from globaleaks import models, security, LANGUAGES_SUPPORTED_CODES, LANGUAGES_SUPPORTED
from globaleaks.db.datainit import db_update_memory_variables
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import transport_security_check, authenticated
from globaleaks.rest import errors, requests
from globaleaks.rest.apicache import GLApiCache
from globaleaks.settings import transact, transact_ro, GLSettings
from globaleaks.utils.structures import fill_localized_keys, get_localized_values
from globaleaks.utils.utility import log


def db_admin_serialize_node(store, language):
    node = store.find(models.Node).one()

    # Contexts and Receivers relationship
    configured  = store.find(models.ReceiverContext).count() > 0

    custom_homepage = os.path.isfile(os.path.join(GLSettings.static_path, "custom_homepage.html"))

    ret_dict = {
        'name': node.name,
        'presentation': node.presentation,
        'hidden_service': node.hidden_service,
        'public_site': node.public_site,
        'email': node.email,
        'version': GLSettings.version_string,
        'languages_supported': LANGUAGES_SUPPORTED,
        'languages_enabled': node.languages_enabled,
        'default_language' : node.default_language,
        'default_timezone' : node.default_timezone,
        'maximum_filesize': node.maximum_filesize,
        'maximum_namesize': node.maximum_namesize,
        'maximum_textsize': node.maximum_textsize,
        'tor2web_admin': GLSettings.memory_copy.tor2web_admin,
        'tor2web_custodian': GLSettings.memory_copy.tor2web_custodian,
        'tor2web_whistleblower': GLSettings.memory_copy.tor2web_whistleblower,
        'tor2web_receiver': GLSettings.memory_copy.tor2web_receiver,
        'tor2web_unauth': GLSettings.memory_copy.tor2web_unauth,
        'submission_minimum_delay' : GLSettings.memory_copy.submission_minimum_delay,
        'submission_maximum_ttl' : GLSettings.memory_copy.submission_maximum_ttl,
        'can_postpone_expiration': node.can_postpone_expiration,
        'can_delete_submission': node.can_delete_submission,
        'ahmia': node.ahmia,
        'allow_unencrypted': node.allow_unencrypted,
        'allow_iframes_inclusion': node.allow_iframes_inclusion,
        'wizard_done': node.wizard_done,
        'configured': configured,
        'password': u'',
        'old_password': u'',
        'custom_homepage': custom_homepage,
        'disable_privacy_badge': node.disable_privacy_badge,
        'disable_security_awareness_badge': node.disable_security_awareness_badge,
        'disable_security_awareness_questions': node.disable_security_awareness_questions,
        'disable_key_code_hint': node.disable_key_code_hint,
        'simplified_login': node.simplified_login,
        'graph_captcha': node.graph_captcha,
        'human_captcha': node.human_captcha,
        'proof_of_work': node.proof_of_work,
        'enable_custom_privacy_badge': node.enable_custom_privacy_badge,
        'landing_page': node.landing_page,
        'show_contexts_in_alphabetical_order': node.show_contexts_in_alphabetical_order
    }

    return get_localized_values(ret_dict, node, models.Node.localized_strings, language)


@transact_ro
def admin_serialize_node(store, language):
    return db_admin_serialize_node(store, language)


def db_update_node(store, request, wizard_done, language):
    """
    Update and serialize the node infos

    :param store: the store on which perform queries.
    :param language: the language in which to localize data
    :return: a dictionary representing the serialization of the node
    """
    node = store.find(models.Node).one()

    fill_localized_keys(request, models.Node.localized_strings, language)

    admin = store.find(models.User, (models.User.username == unicode('admin'))).one()

    password = request.get('password', None)
    old_password = request.get('old_password', None)

    if password and old_password and len(password) and len(old_password):
        admin.password = security.change_password(admin.password,
                                    old_password, password, admin.salt)

    # verify that the languages enabled are valid 'code' in the languages supported
    node.languages_enabled = []
    for lang_code in request['languages_enabled']:
        if lang_code in LANGUAGES_SUPPORTED_CODES:
            node.languages_enabled.append(lang_code)
        else:
            raise errors.InvalidInputFormat("Invalid lang code enabled: %s" % lang_code)

    if not len(node.languages_enabled):
        raise errors.InvalidInputFormat("Missing enabled languages")

    # enforcing of default_language usage (need to be set, need to be _enabled)
    if request['default_language']:
        if request['default_language'] not in node.languages_enabled:
            raise errors.InvalidInputFormat("Invalid lang code as default")

        node.default_language = request['default_language']

    else:
        node.default_language = node.languages_enabled[0]
        log.err("Default language not set!? fallback on %s" % node.default_language)

    if wizard_done:
        node.wizard_done = True

    node.update(request)

    db_update_memory_variables(store)

    return db_admin_serialize_node(store, language)


@transact
def update_node(*args):
    return db_update_node(*args)


class NodeInstance(BaseHandler):
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self):
        """
        Get the node infos.

        Parameters: None
        Response: AdminNodeDesc
        """
        node_description = yield admin_serialize_node(self.request.language)
        self.set_status(200)
        self.finish(node_description)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def put(self):
        """
        Update the node infos.

        Request: AdminNodeDesc
        Response: AdminNodeDesc
        Errors: InvalidInputFormat
        """
        request = self.validate_message(self.request.body,
                                        requests.AdminNodeDesc)

        node_description = yield update_node(request, True, self.request.language)
        GLApiCache.invalidate()

        self.set_status(202) # Updated
        self.finish(node_description)
