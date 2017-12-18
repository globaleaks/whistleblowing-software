# -*- coding: utf-8
# custodian
# ********
#
# Implement the classes handling the requests performed to /custodian/* URI PATH
from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.rest import requests
from globaleaks.utils.utility import datetime_to_ISO8601, datetime_now


def serialize_identityaccessrequest(store, tid, identityaccessrequest):
    itip, user = store.find((models.InternalTip, models.User),
                            models.InternalTip.id == models.ReceiverTip.internaltip_id,
                            models.User.id == models.ReceiverTip.receiver_id,
                            models.ReceiverTip.id == identityaccessrequest.receivertip_id,
                            models.User.tid == tid).one()

    reply_user = store.find(models.User,
                            models.User.id == identityaccessrequest.reply_user_id,
                            tid=tid).one()

    return {
        'id': identityaccessrequest.id,
        'receivertip_id': identityaccessrequest.receivertip_id,
        'request_date': datetime_to_ISO8601(identityaccessrequest.request_date),
        'request_user_name': user.name,
        'request_motivation': identityaccessrequest.request_motivation,
        'reply_date': datetime_to_ISO8601(identityaccessrequest.reply_date),
        'reply_user_name': reply_user.id if reply_user is not None else '',
        'reply': identityaccessrequest.reply,
        'reply_motivation': identityaccessrequest.reply_motivation,
        'submission_date': datetime_to_ISO8601(itip.creation_date)
    }



def db_get_identityaccessrequest_list(store, tid, rtip_id):
    return [serialize_identityaccessrequest(store, tid, iar) for iar in store.find(models.IdentityAccessRequest, receivertip_id=rtip_id, tid=tid)]


@transact
def get_identityaccessrequest_list(store, tid):
    return [serialize_identityaccessrequest(store, tid, iar)
        for iar in store.find(models.IdentityAccessRequest, models.IdentityAccessRequest.reply == u'pending', tid=tid)]


@transact
def get_identityaccessrequest(store, tid, identityaccessrequest_id):
    iar = store.find(models.IdentityAccessRequest,
                     models.IdentityAccessRequest.id == identityaccessrequest_id, tid=tid).one()
    return serialize_identityaccessrequest(store, tid, iar)


@transact
def update_identityaccessrequest(store, tid, user_id, identityaccessrequest_id, request):
    iar, rtip = store.find((models.IdentityAccessRequest, models.ReceiverTip),
                           models.IdentityAccessRequest.id == identityaccessrequest_id,
                           models.ReceiverTip.id == models.IdentityAccessRequest.receivertip_id,
                           models.ReceiverTip.tid == tid).one()

    if iar.reply == 'pending':
        iar.reply_date = datetime_now()
        iar.reply_user_id = user_id
        iar.reply = request['reply']
        iar.reply_motivation = request['reply_motivation']

        if iar.reply == 'authorized':
            rtip.can_access_whistleblower_identity = True

    return serialize_identityaccessrequest(store, tid, iar)


class IdentityAccessRequestInstance(BaseHandler):
    """
    This handler allow custodians to manage an identity access request by a receiver
    """
    check_roles = 'custodian'

    def get(self, identityaccessrequest_id):
        """
        Parameters: the id of the identity access request
        Response: IdentityAccessRequestDesc
        Errors: IdentityAccessRequestIdNotFound, InvalidInputFormat, InvalidAuthentication
        """
        return get_identityaccessrequest(self.request.tid, identityaccessrequest_id)

    def put(self, identityaccessrequest_id):
        """
        Parameters: the id of the identity access request
        Request: IdentityAccessRequestDesc
        Response: IdentityAccessRequestDesc
        Errors: IdentityAccessRequestIdNotFound, InvalidInputFormat, InvalidAuthentication
        """
        request = self.validate_message(self.request.content.read(), requests.CustodianIdentityAccessRequestDesc)

        return update_identityaccessrequest(self.request.tid,
                                            self.current_user.user_id,
                                            identityaccessrequest_id,
                                            request)


class IdentityAccessRequestsCollection(BaseHandler):
    """
    This interface return the list of the requests of access to whislteblower identities
    GET /identityrequests
    """
    check_roles = 'custodian'

    def get(self):
        """
        Response: identityaccessrequestsList
        Errors: InvalidAuthentication
        """
        return get_identityaccessrequest_list(self.request.tid)
