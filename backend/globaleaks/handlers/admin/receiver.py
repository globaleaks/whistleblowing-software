# -*- coding: utf-8
#
#   /admin/receivers
#   *****
# Implementation of the code executed on handler /admin/receivers
#
from globaleaks import models
from globaleaks.handlers.admin.user import admin_serialize_receiver
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.rest import requests
from globaleaks.utils.structures import fill_localized_keys


@transact
def get_receiver_list(store, tid, language):
    """
    Returns:
        (list) the list of receivers
    """
    return [admin_serialize_receiver(store, receiver, user, language)
        for receiver, user in store.find((models.Receiver, models.User),
                                          models.User.tid == tid,
                                          models.Receiver.id == models.User.id)]


def db_get_receiver(store, tid, receiver_id):
    """
    Returns:
        (dict) the receiver

    """
    return models.db_get(store,
                         (models.Receiver, models.User),
                          models.Receiver.id == receiver_id,
                          models.User.id == receiver_id,
                          models.User.tid == tid)


@transact
def get_receiver(store, tid, receiver_id, language):
    receiver, user = db_get_receiver(store, tid, receiver_id)
    return admin_serialize_receiver(store, receiver, user, language)


@transact
def update_receiver(store, tid, receiver_id, request, language):
    """
    Updates the specified receiver with the details.
    """
    fill_localized_keys(request, models.Receiver.localized_keys, language)

    receiver, user = db_get_receiver(store, tid, receiver_id)

    receiver.update(request)

    return admin_serialize_receiver(store, receiver, user, language)


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
        return get_receiver_list(self.request.tid, self.request.language)


class ReceiverInstance(BaseHandler):
    check_roles = 'admin'
    invalidate_cache = True

    def put(self, receiver_id):
        """
        Update the specified receiver.

        Parameters: receiver_id
        Request: AdminReceiverDesc
        Response: AdminReceiverDesc
        """
        request = self.validate_message(self.request.content.read(), requests.AdminReceiverDesc)

        return update_receiver(self.request.tid, receiver_id, request, self.request.language)
