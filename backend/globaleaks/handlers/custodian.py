# -*- coding: utf-8 -*-
#
# Handlers dealing with custodian user functionalities
from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.rest import requests
from globaleaks.utils.utility import datetime_to_ISO8601, datetime_now


def serialize_identityaccessrequest(session, tid, identityaccessrequest):
    itip, user = session.query(models.InternalTip, models.User) \
                      .filter(models.InternalTip.id == models.ReceiverTip.internaltip_id,
                              models.ReceiverTip.id == identityaccessrequest.receivertip_id,
                              models.ReceiverTip.receiver_id == models.User.id,
                              models.User.tid == tid).one()

    reply_user = session.query(models.User) \
                      .filter(models.User.id == identityaccessrequest.reply_user_id,
                              models.User.tid == tid).one_or_none()
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



def db_get_identityaccessrequest_list(session, tid, rtip_id):
    return [serialize_identityaccessrequest(session, tid, iar) for iar in session.query(models.IdentityAccessRequest).filter(models.IdentityAccessRequest.receivertip_id == rtip_id)]


@transact
def get_identityaccessrequest_list(session, tid):
    return [serialize_identityaccessrequest(session, tid, iar)
        for iar in session.query(models.IdentityAccessRequest).filter(models.IdentityAccessRequest.reply == u'pending',
                                                                      models.IdentityAccessRequest.receivertip_id == models.ReceiverTip.id,
                                                                      models.ReceiverTip.internaltip_id == models.InternalTip.id,
                                                                      models.InternalTip.tid == tid)]


@transact
def get_identityaccessrequest(session, tid, identityaccessrequest_id):
    iar = session.query(models.IdentityAccessRequest) \
               .filter(models.IdentityAccessRequest.id == identityaccessrequest_id,
                       models.IdentityAccessRequest.receivertip_id == models.ReceiverTip.id,
                       models.ReceiverTip.internaltip_id == models.InternalTip.id,
                       models.InternalTip.tid == tid).one()


    return serialize_identityaccessrequest(session, tid, iar)


@transact
def update_identityaccessrequest(session, tid, user_id, identityaccessrequest_id, request):
    iar, rtip = session.query(models.IdentityAccessRequest, models.ReceiverTip) \
                       .filter(models.IdentityAccessRequest.id == identityaccessrequest_id,
                               models.ReceiverTip.id == models.IdentityAccessRequest.receivertip_id,
                               models.ReceiverTip.internaltip_id == models.InternalTip.id,
                               models.InternalTip.tid == tid).one()

    if iar.reply == 'pending':
        iar.reply_date = datetime_now()
        iar.reply_user_id = user_id
        iar.reply = request['reply']
        iar.reply_motivation = request['reply_motivation']

        if iar.reply == 'authorized':
            rtip.can_access_whistleblower_identity = True

    return serialize_identityaccessrequest(session, tid, iar)


class IdentityAccessRequestInstance(BaseHandler):
    """
    This handler allow custodians to manage an identity access request by a receiver
    """
    check_roles = 'custodian'

    def get(self, identityaccessrequest_id):
        return get_identityaccessrequest(self.request.tid, identityaccessrequest_id)

    def put(self, identityaccessrequest_id):
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
        return get_identityaccessrequest_list(self.request.tid)
