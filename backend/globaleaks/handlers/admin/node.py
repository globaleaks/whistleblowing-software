# -*- coding: UTF-8
#
#   /admin/node
#   *****
# Implementation of the code executed on handler /admin/node
#
import os

from twisted.internet.defer import inlineCallbacks

from globaleaks import models, utils, LANGUAGES_SUPPORTED_CODES, LANGUAGES_SUPPORTED
from globaleaks.db.appdata import load_appdata
from globaleaks.db import db_refresh_memory_variables
from globaleaks.models.l10n import EnabledLanguage, Node_L10N
from globaleaks.models.config import ConfigFactory
from globaleaks.orm import transact, transact_ro
from globaleaks.handlers.base import BaseHandler
from globaleaks.rest import errors, requests
from globaleaks.rest.apicache import GLApiCache
from globaleaks.security import hash_password
from globaleaks.settings import GLSettings
from globaleaks.utils.structures import fill_localized_keys, get_localized_values
from globaleaks.utils.utility import log


def db_admin_serialize_node(store, language):
    c_node = ConfigFactory('node', store)
    c_node.fill_object_dict()

    ret_dict = {
        'name': c_node.ro.name,
        'hidden_service': c_node.ro.hidden_service,
        'public_site': c_node.ro.public_site,
        'version': c_node.ro.version,
        'version_db': c_node.ro.version_db,
        'default_language': c_node.ro.default_language,
        'default_timezone': c_node.ro.default_timezone,
        'default_password': c_node.ro.default_password,
        'maximum_filesize': c_node.ro.maximum_filesize,
        'maximum_namesize': c_node.ro.maximum_namesize,
        'maximum_textsize': c_node.ro.maximum_textsize,
        'tor2web_admin': c_node.ro.tor2web_admin,
        'tor2web_custodian': c_node.ro.tor2web_custodian,
        'tor2web_whistleblower': c_node.ro.tor2web_whistleblower,
        'tor2web_receiver': c_node.ro.tor2web_receiver,
        'tor2web_unauth': c_node.ro.tor2web_unauth,
        'submission_minimum_delay': c_node.ro.submission_minimum_delay,
        'submission_maximum_ttl': c_node.ro.submission_maximum_ttl,
        'can_postpone_expiration': c_node.ro.can_postpone_expiration,
        'can_delete_submission': c_node.ro.can_delete_submission,
        'can_grant_permissions': c_node.ro.can_grant_permissions,
        'ahmia': c_node.ro.ahmia,
        'allow_indexing': c_node.ro.allow_indexing,
        'allow_unencrypted': c_node.ro.allow_unencrypted,
        'disable_encryption_warnings': c_node.ro.disable_encryption_warnings,
        'allow_iframes_inclusion': c_node.ro.allow_iframes_inclusion,
        'wizard_done': c_node.ro.wizard_done,
        'disable_submissions': c_node.ro.disable_submissions,
        'disable_privacy_badge': c_node.ro.disable_privacy_badge,
        'disable_security_awareness_badge': c_node.ro.disable_security_awareness_badge,
        'disable_security_awareness_questions': c_node.ro.disable_security_awareness_questions,
        'disable_key_code_hint': c_node.ro.disable_key_code_hint,
        'disable_donation_panel': c_node.ro.disable_donation_panel,
        'simplified_login': c_node.ro.simplified_login,
        'enable_captcha': c_node.ro.enable_captcha,
        'enable_proof_of_work': c_node.ro.enable_proof_of_work,
        'enable_experimental_features': c_node.ro.enable_experimental_features,
        'enable_custom_privacy_badge': c_node.ro.enable_custom_privacy_badge,
        'landing_page': c_node.ro.landing_page,
        'context_selector_type': c_node.ro.context_selector_type,
        'show_contexts_in_alphabetical_order': c_node.ro.show_contexts_in_alphabetical_order,
        'show_small_context_cards': c_node.ro.show_small_context_cards,
        'threshold_free_disk_megabytes_high': c_node.ro.threshold_free_disk_megabytes_high,
        'threshold_free_disk_megabytes_medium': c_node.ro.threshold_free_disk_megabytes_medium,
        'threshold_free_disk_megabytes_low': c_node.ro.threshold_free_disk_megabytes_low,
        'threshold_free_disk_percentage_high': c_node.ro.threshold_free_disk_percentage_high,
        'threshold_free_disk_percentage_medium': c_node.ro.threshold_free_disk_percentage_medium,
        'threshold_free_disk_percentage_low': c_node.ro.threshold_free_disk_percentage_low,
        'wbtip_timetolive': c_node.ro.wbtip_timetolive,
        'basic_auth': c_node.ro.basic_auth,
        'basic_auth_username': c_node.ro.basic_auth_username,
        'basic_auth_password': c_node.ro.basic_auth_password,
    }


    # Contexts and Receivers relationship
    configured  = store.find(models.ReceiverContext).count() > 0
    custom_homepage = os.path.isfile(os.path.join(GLSettings.static_path, "custom_homepage.html"))

    misc_dict = {
        'languages_supported': LANGUAGES_SUPPORTED,
        'languages_enabled': EnabledLanguage.get_all_strs(store),
        'configured': configured,
        'custom_homepage': custom_homepage,
    }

    l10n_dict = Node_L10N(store).build_localized_dict(language)
    return utils.sets.disjoint_union(ret_dict, misc_dict, l10n_dict)


@transact_ro
def admin_serialize_node(store, language):
    return db_admin_serialize_node(store, language)


def enable_disable_languages(store, request):
    cur_enabled_langs = EnabledLanguage.get_all_strs(store)
    new_enabled_langs = [unicode(y) for y in request['languages_enabled']]

    if len(new_enabled_langs) < 1:
        raise errors.InvalidInputFormat("No languages enabled!")

    if request['default_language'] not in new_enabled_langs:
        raise errors.InvalidInputFormat("Invalid lang code for chosen default_language")

    appdata = None
    for lang_code in new_enabled_langs:
        if lang_code not in LANGUAGES_SUPPORTED_CODES:
            raise errors.InvalidInputFormat("Invalid lang code: %s" % lang_code)
        if lang_code not in cur_enabled_langs:
            if appdata is None:
              appdata = load_appdata()
            log.debug("Adding a new lang %s" % lang_code)
            EnabledLanguage.add_new_lang(store, lang_code, appdata)

    for lang_code in cur_enabled_langs:
        if lang_code not in new_enabled_langs:
            EnabledLanguage.remove_old_lang(store, lang_code)


def db_update_node(store, request, language):
    """
    Update and serialize the node infos

    :param store: the store on which perform queries.
    :param language: the language in which to localize data
    :return: a dictionary representing the serialization of the node
    """
    enable_disable_languages(store, request)

    node_l10n = Node_L10N(store)
    node_l10n.update_model(request, language)

    c_node = ConfigFactory('node', store)
    c_node.fill_object_dict()

    c_node.w.basic_auth.raw_value = request['basic_auth']
    c_node.update(request)

    if request['basic_auth'] and request['basic_auth_username'] != '' and request['basic_auth_password']  != '':
        c_node.w.basic_auth.raw_value = True
        c_node.w.basic_auth_username.raw_value = request['basic_auth_username']
        c_node.w.basic_auth_password.raw_value = request['basic_auth_password']
    else:
        c_node.w.basic_auth.raw_value = False

    db_refresh_memory_variables(store)

    return db_admin_serialize_node(store, language)


@transact
def update_node(*args):
    return db_update_node(*args)


class NodeInstance(BaseHandler):
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def get(self):
        """
        Get the node infos.

        Parameters: None
        Response: AdminNodeDesc
        """
        node_description = yield admin_serialize_node(self.request.language)
        self.write(node_description)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
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

        node_description = yield update_node(request, self.request.language)
        GLApiCache.invalidate()

        self.set_status(202) # Updated
        self.write(node_description)
