# -*- coding: UTF-8
#
#   /admin/receiver
#   *****
# Implementation of the code executed on handler /admin/receiver
#

import os
import shutil

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import transport_security_check, authenticated, unauthenticated
from globaleaks.handlers.admin.user import *
from globaleaks.rest import errors, requests
from globaleaks.rest.apicache import GLApiCache
from globaleaks.settings import transact, transact_ro, GLSettings
from globaleaks.utils.structures import fill_localized_keys, get_localized_values
from globaleaks.utils.utility import log, datetime_now, datetime_null, datetime_to_ISO8601


def admin_serialize_receiver(receiver, language):
    """
    Serialize the specified receiver

    :param language: the language in which to localize data
    :return: a dictionary representing the serialization of the receiver
    """
    ret_dict = {
        'id': receiver.id,
        'name': receiver.user.name,
        'can_delete_submission': receiver.can_delete_submission,
        'can_postpone_expiration': receiver.can_postpone_expiration,
        'username': receiver.user.username,
        'mail_address': receiver.user.mail_address,
        'ping_mail_address': receiver.ping_mail_address,
        'password': u'',
        'state': receiver.user.state,
        'configuration': receiver.configuration,
        'contexts': [c.id for c in receiver.contexts],
        'pgp_key_info': receiver.user.pgp_key_info,
        'pgp_key_public': receiver.user.pgp_key_public,
        'pgp_key_remove': False,
        'pgp_key_fingerprint': receiver.user.pgp_key_fingerprint,
        'pgp_key_expiration': datetime_to_ISO8601(receiver.user.pgp_key_expiration),
        'pgp_key_status': receiver.user.pgp_key_status,
        'tip_notification': receiver.tip_notification,
        'ping_notification': receiver.ping_notification,
        'presentation_order': receiver.presentation_order,
        'language': receiver.user.language,
        'timezone': receiver.user.timezone,
        'tip_expiration_threshold': receiver.tip_expiration_threshold,
        'password_change_needed': receiver.user.password_change_needed,
    }

    # description and eventually other localized strings should be taken from user model
    get_localized_values(ret_dict, receiver.user, ['description'], language)

    return get_localized_values(ret_dict, receiver, receiver.localized_strings, language)


@transact_ro
def get_receiver_list(store, language):
    """
    Returns:
        (list) the list of receivers
    """
    receiver_list = []

    receivers = store.find(models.Receiver)

    for receiver in receivers:
        receiver_list.append(admin_serialize_receiver(receiver, language))

    return receiver_list


def create_random_receiver_portrait(receiver_uuid):
    """
    By default take a picture and put in the receiver face,
    """
    try:
        shutil.copy(
            os.path.join(GLSettings.static_source, "default-profile-picture.png"),
            os.path.join(GLSettings.static_path, "%s.png" % receiver_uuid)
        )
    except Exception as excep:
        log.err("Unable to copy default receiver portrait in a new receiver! %s" % excep.message)
        raise excep


def db_create_receiver(store, request, language):
    """
    Creates a new receiver.
    Returns:
        (dict) the configured receiver
    """
    user = db_create_user(store, request, language)

    fill_localized_keys(request, models.Receiver.localized_strings, language)

    receiver = models.Receiver(request)

    # Set receiver.id = receiver.user.username = receiver.user.id
    receiver.id = user.username = user.id

    store.add(receiver)

    create_random_receiver_portrait(receiver.id)

    contexts = request.get('contexts', [])
    for context_id in contexts:
        context = models.Context.get(store, context_id)
        if not context:
            log.err("Creation error: invalid Context can't be associated")
            raise errors.ContextIdNotFound
        context.receivers.add(receiver)

    log.debug("Created new receiver")

    return receiver


@transact
def create_receiver(store, request, language):
    receiver = db_create_receiver(store, request, language)
    return admin_serialize_receiver(receiver, language)


def db_get_receiver(store, receiver_id):
    """
    raises :class:`globaleaks.errors.ReceiverIdNotFound` if the receiver does
    not exist.
    Returns:
        (dict) the receiver

    """
    receiver = models.Receiver.get(store, receiver_id)

    if not receiver:
        raise errors.ReceiverIdNotFound

    return receiver


@transact_ro
def get_receiver(store, receiver_id, language):
    receiver = db_get_receiver(store, receiver_id)
    return admin_serialize_receiver(receiver, language)


@transact
def update_receiver(store, receiver_id, request, language):
    """
    Updates the specified receiver with the details.
    raises :class:`globaleaks.errors.ReceiverIdNotFound` if the receiver does
    not exist.
    """
    db_update_user(store, receiver_id, request, language)

    receiver = models.Receiver.get(store, receiver_id)

    if not receiver:
        raise errors.ReceiverIdNotFound

    fill_localized_keys(request, models.Receiver.localized_strings, language)

    contexts = request.get('contexts', [])

    for context in receiver.contexts:
        receiver.contexts.remove(context)

    for context_id in contexts:
        context = models.Context.get(store, context_id)
        if not context:
            raise errors.ContextIdNotFound

        receiver.contexts.add(context)

    receiver.update(request)

    return admin_serialize_receiver(receiver, language)


@transact
def delete_receiver(store, receiver_id):
    receiver = db_get_receiver(store, receiver_id)

    portrait = os.path.join(GLSettings.static_path, "%s.png" % receiver_id)
    if os.path.exists(portrait):
        os.remove(portrait)

    store.remove(receiver.user)


class ReceiversCollection(BaseHandler):
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self):
        """
        Return all the receivers.

        Parameters: None
        Response: adminReceiverList
        Errors: None
        """
        response = yield get_receiver_list(self.request.language)

        self.set_status(200)
        self.finish(response)


class ReceiverCreate(BaseHandler):
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def post(self):
        """
        Get the specified receiver.

        Request: AdminReceiverDesc
        Response: AdminReceiverDesc
        Errors: InvalidInputFormat, ContextIdNotFound
        """
        request = self.validate_message(self.request.body,
                                        requests.AdminReceiverDesc)

        response = yield create_receiver(request, self.request.language)
        GLApiCache.invalidate()

        self.set_status(201) # Created
        self.finish(response)


class ReceiverInstance(BaseHandler):
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, receiver_id):
        """
        Get the specified receiver.

        Parameters: receiver_id
        Response: AdminReceiverDesc
        Errors: InvalidInputFormat, ReceiverIdNotFound
        """
        response = yield get_receiver(receiver_id, self.request.language)

        self.set_status(200)
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def put(self, receiver_id):
        """
        Update the specified receiver.

        Parameters: receiver_id
        Request: AdminReceiverDesc
        Response: AdminReceiverDesc
        Errors: InvalidInputFormat, ReceiverIdNotFound, ContextId
        """
        request = self.validate_message(self.request.body, requests.AdminReceiverDesc)

        response = yield update_receiver(receiver_id, request, self.request.language)
        GLApiCache.invalidate()

        self.set_status(201)
        self.finish(response)

    @inlineCallbacks
    @transport_security_check('admin')
    @authenticated('admin')
    def delete(self, receiver_id):
        """
        Delete the specified receiver.

        Parameters: receiver_id
        Request: None
        Response: None
        Errors: InvalidInputFormat, ReceiverIdNotFound
        """
        yield delete_receiver(receiver_id)

        # get the updated list of receivers, and update the cache
        GLApiCache.invalidate()

        self.set_status(200) # OK and return not content
        self.finish()
