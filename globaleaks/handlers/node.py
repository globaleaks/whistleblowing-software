# -*- coding: UTF-8
#   node
#   ****
#
# Implementation of classes handling the HTTP request to /node, public
# exposed API.

import os

from twisted.internet.defer import inlineCallbacks

from globaleaks.utils.utility import log, datetime_to_ISO8601
from globaleaks.utils.structures import Rosetta, Fields
from globaleaks.settings import transact_ro, GLSetting, stats_counter
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import transport_security_check, unauthenticated
from globaleaks import models, LANGUAGES_SUPPORTED

@transact_ro
def anon_serialize_node(store, language=GLSetting.memory_copy.default_language):
    node = store.find(models.Node).one()

    # Contexts and Receivers relationship
    associated = store.find(models.ReceiverContext).count()

    custom_homepage = False

    try: 
        custom_homepage = os.path.isfile(os.path.join(GLSetting.static_path, "custom_homepage.html"))
    except:
        pass

    node_dict = {
      'name': node.name,
      'hidden_service': node.hidden_service,
      'public_site': node.public_site,
      'email': node.email,
      'languages_enabled': node.languages_enabled,
      'languages_supported': LANGUAGES_SUPPORTED,
      'default_language' : node.default_language,
      # extended settings info:
      'maximum_namesize': node.maximum_namesize,
      'maximum_textsize': node.maximum_textsize,
      'maximum_filesize': node.maximum_filesize,
      # public serialization use GLSetting memory var, and
      # not the real one, because needs to bypass
      # Tor2Web unsafe deny default settings
      'tor2web_admin': GLSetting.memory_copy.tor2web_admin,
      'tor2web_submission': GLSetting.memory_copy.tor2web_submission,
      'tor2web_receiver': GLSetting.memory_copy.tor2web_receiver,
      'tor2web_unauth': GLSetting.memory_copy.tor2web_unauth,
      'ahmia': node.ahmia,
      'postpone_superpower': node.postpone_superpower,
      'can_delete_submission': node.can_delete_submission,
      'wizard_done': node.wizard_done,
      'anomaly_checks': node.anomaly_checks,
      'allow_unencrypted': node.allow_unencrypted,
      'x_frame_options_mode': node.x_frame_options_mode,
      'x_frame_options_allow_from': node.x_frame_options_allow_from,
      'receipt_regexp': node.receipt_regexp,
      'configured': True if associated else False,
      'password': u"",
      'old_password': u"",
      'custom_homepage': custom_homepage,
      'disable_privacy_badge': node.disable_privacy_badge,
      'disable_security_awareness_questions': node.disable_security_awareness_questions
    }

    mo = Rosetta()
    mo.acquire_storm_object(node)
    for attr in mo.get_localized_attrs():
        node_dict[attr] = mo.dump_translated(attr, language)

    return node_dict

def anon_serialize_context(context, language=GLSetting.memory_copy.default_language):
    """
    @param context: a valid Storm object
    @return: a dict describing the contexts available for submission,
        (e.g. checks if almost one receiver is associated)
    """

    mo = Rosetta()
    mo.acquire_storm_object(context)
    fo = Fields(context.localized_fields, context.unique_fields)

    context_dict = {
        "id": context.id,
        "escalation_threshold": 0,
        "file_max_download": context.file_max_download,
        "file_required": context.file_required,
        "selectable_receiver": context.selectable_receiver,
        "tip_max_access": context.tip_max_access,
        "tip_timetolive": context.tip_timetolive,
        "submission_introduction": u'NYI', # unicode(context.submission_introduction), # optlang
        "submission_disclaimer": u'NYI', # unicode(context.submission_disclaimer), # optlang
        "select_all_receivers": context.select_all_receivers,
        "maximum_selectable_receivers": context.maximum_selectable_receivers,
        'require_pgp': context.require_pgp,
        "show_small_cards": context.show_small_cards,
        "show_receivers": context.show_receivers,
        "enable_private_messages": context.enable_private_messages,
        "presentation_order": context.presentation_order,
                     # list is needed because .values returns a generator
        "receivers": list(context.receivers.values(models.Receiver.id)),
        'name': mo.dump_translated('name', language),
        "description": mo.dump_translated('description', language),
        "fields": fo.dump_fields(language)
    }

    if not len(context_dict['receivers']):
        return None

    return context_dict


def anon_serialize_receiver(receiver, language=GLSetting.memory_copy.default_language):
    """
    @param receiver: a valid Storm object
    @return: a dict describing the receivers available in the node
        (e.g. checks if almost one context is associated, or, in
         node where GPG encryption is enforced, that a valid key is registered)
    """
    mo = Rosetta()
    mo.acquire_storm_object(receiver)

    receiver_dict = {
        "creation_date": datetime_to_ISO8601(receiver.creation_date),
        "update_date": datetime_to_ISO8601(receiver.last_update),
        "name": receiver.name,
        "description": mo.dump_translated('description', language),
        "id": receiver.id,
        "receiver_level": receiver.receiver_level,
        "tags": receiver.tags,
        "presentation_order": receiver.presentation_order,
        "gpg_key_status": receiver.gpg_key_status,
                    # list is needed because .values returns a generator
        "contexts": list(receiver.contexts.values(models.Context.id))
    }

    if not len(receiver_dict['contexts']):
        return None

    return receiver_dict


class InfoCollection(BaseHandler):
    """
    U1
    Returns information on the GlobaLeaks node. This includes submission
    parameters (contexts description, fields, public receiver list).
    Contains System-wide properties.
    """

    @transport_security_check("unauth")
    @unauthenticated
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: publicNodeDesc
        Errors: NodeNotFound
        """
        stats_counter('anon_requests')
        response = yield anon_serialize_node(self.request.language)
        self.finish(response)


class AhmiaDescriptionHandler(BaseHandler):
    """
    Description of Ahmia 'protocol' is in:
    https://ahmia.fi/documentation/
    and we're supporting the Hidden Service description proposal from:
    https://ahmia.fi/documentation/descriptionProposal/
    """

    @transport_security_check("unauth")
    @unauthenticated
    @inlineCallbacks
    def get(self, *uriargs):

        log.debug("Requested Ahmia description file")
        node_info = yield anon_serialize_node(self.request.language)

        if node_info['ahmia']:

            ahmia_description = {
                "title": node_info['name'],
                "description": node_info['description'],
                # we've not yet keywords, need to add them in Node ?
                "keywords": "%s (GlobaLeaks instance)" % node_info['name'],
                "relation": node_info['public_site'],
                "language": node_info['default_language'],
                "contactInformation": u'', # we've removed Node.email_addr
                "type": "GlobaLeaks"
            }

            self.finish(ahmia_description)

        else: # in case of disabled option we return 404

            self.set_status(404)


@transact_ro
def get_public_context_list(store, default_lang):
    context_list = []
    contexts = store.find(models.Context)

    for context in contexts:
        context_desc = anon_serialize_context(context, default_lang)
        # context not yet ready for submission return None
        if context_desc:
            context_list.append(context_desc)

    return context_list


class ContextsCollection(BaseHandler):
    """
    Return the public list of contexts, those information are shown in client
    and would be memorized in a third party indexer service. This is way some dates
    are returned within.
    """
    @transport_security_check("unauth")
    @unauthenticated
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: publicContextList
        Errors: None
        """
        stats_counter('anon_requests')
        response = yield get_public_context_list(self.request.language)
        self.finish(response)

@transact_ro
def get_public_receiver_list(store, default_lang):
    receiver_list = []
    receivers = store.find(models.Receiver)

    for receiver in receivers:
        receiver_desc = anon_serialize_receiver(receiver, default_lang)
        # receiver not yet ready for submission return None
        if receiver_desc:
            receiver_list.append(receiver_desc)

    return receiver_list

class ReceiversCollection(BaseHandler):
    """
    Return the description of all the receivers visible from the outside.
    """

    @transport_security_check("unauth")
    @unauthenticated
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: publicReceiverList
        Errors: None
        """
        stats_counter('anon_requests')
        response = yield get_public_receiver_list(self.request.language)
        self.finish(response)
