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
def get_receiver_list(session, tid, language):
    return [admin_serialize_receiver(session, receiver, user, language)
        for receiver, user in session.query(models.Receiver, models.User) \
                                     .filter(models.Receiver.id == models.User.id, \
                                             models.User.tid == tid) \
                                     .order_by(models.User.id)]


def db_get_receiver(session, tid, receiver_id):
    return models.db_get(session,
                         (models.Receiver, models.User),
                          models.Receiver.id == receiver_id,
                          models.User.id == receiver_id,
                          models.User.tid == tid)


@transact
def get_receiver(session, tid, receiver_id, language):
    receiver, user = db_get_receiver(session, tid, receiver_id)
    return admin_serialize_receiver(session, receiver, user, language)


@transact
def update_receiver(session, tid, receiver_id, request, language):
    """
    Updates the specified receiver with the details.
    """
    fill_localized_keys(request, models.Receiver.localized_keys, language)

    receiver, user = db_get_receiver(session, tid, receiver_id)

    receiver.update(request)

    return admin_serialize_receiver(session, receiver, user, language)


class ReceiversCollection(BaseHandler):
    check_roles = 'admin'
    cache_resource = True

    def get(self):
        """
        Return all the receivers.
        """
        return get_receiver_list(self.request.tid, self.request.language)


class ReceiverInstance(BaseHandler):
    check_roles = 'admin'
    invalidate_cache = True

    def put(self, receiver_id):
        """
        Update the specified receiver.
        """
        request = self.validate_message(self.request.content.read(), requests.AdminReceiverDesc)

        return update_receiver(self.request.tid, receiver_id, request, self.request.language)
