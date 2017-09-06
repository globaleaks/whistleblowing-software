# -*- coding: UTF-8
#
#   /admin/receivers
#   *****
# Implementation of the code executed on handler /admin/receivers
#
from globaleaks import models
from globaleaks.handlers.admin.user import db_associate_context_receivers, admin_serialize_receiver
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.user import user_serialize_user
from globaleaks.orm import transact
from globaleaks.rest import errors, requests
from globaleaks.settings import GLSettings
from globaleaks.utils.structures import fill_localized_keys


@transact
def get_receiver_list(store, language):
    """
    Returns:
        (list) the list of receivers
    """
    return [admin_serialize_receiver(store, receiver, language)
        for receiver in store.find(models.Receiver)]


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


@transact
def get_receiver(store, receiver_id, language):
    return admin_serialize_receiver(store, db_get_receiver(store, receiver_id), language)


@transact
def update_receiver(store, receiver_id, request, language):
    """
    Updates the specified receiver with the details.
    raises :class:`globaleaks.errors.ReceiverIdNotFound` if the receiver does
    not exist.
    """
    receiver = models.Receiver.get(store, receiver_id)
    if not receiver:
        raise errors.ReceiverIdNotFound

    fill_localized_keys(request, models.Receiver.localized_keys, language)

    receiver.update(request)

    db_associate_context_receivers(store, receiver, request['contexts'])

    return admin_serialize_receiver(store, receiver, language)


class ReceiversCollection(BaseHandler):
    check_roles = 'admin'
    cache_resource = True

    def get(self):
        """
        Return all the receivers.

        Parameters: None
        Response: adminReceiverList
        Errors: None
        """
        return get_receiver_list(self.request.language)


class ReceiverInstance(BaseHandler):
    check_roles = 'admin'
    invalidate_cache = True

    def put(self, receiver_id):
        """
        Update the specified receiver.

        Parameters: receiver_id
        Request: AdminReceiverDesc
        Response: AdminReceiverDesc
        Errors: InvalidInputFormat, ReceiverIdNotFound, ContextIdNotFound
        """
        request = self.validate_message(self.request.content.read(), requests.AdminReceiverDesc)

        return update_receiver(receiver_id, request, self.request.language)
