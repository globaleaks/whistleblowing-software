# -*- coding: UTF-8
# custodian
# ********
#
# Implement the classes handling the requests performed to /custodian/* URI PATH

from twisted.internet.defer import inlineCallbacks

from globaleaks.orm import transact, transact_ro
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.handlers.base import BaseHandler
from globaleaks.models import IdentityAccessRequest
from globaleaks.rest import requests
from globaleaks.utils.structures import Rosetta
from globaleaks.utils.utility import datetime_to_ISO8601, datetime_now


def serialize_identityaccessrequest(identityaccessrequest, language):
    iar = {
        'id': identityaccessrequest.id,
        'receivertip_id': identityaccessrequest.receivertip_id,
        'request_date': datetime_to_ISO8601(identityaccessrequest.request_date),
        'request_user_name': identityaccessrequest.receivertip.receiver.user.name,
        'request_motivation': identityaccessrequest.request_motivation,
        'reply_date': datetime_to_ISO8601(identityaccessrequest.reply_date),
        'reply_user_name': identityaccessrequest.reply_user.name \
                if identityaccessrequest.reply_user is not None else '',
        'reply': identityaccessrequest.reply,
        'reply_motivation': identityaccessrequest.reply_motivation,
        'submission_date': datetime_to_ISO8601(identityaccessrequest.receivertip.internaltip.creation_date)
    }

    mo = Rosetta(identityaccessrequest.receivertip.internaltip.context.localized_keys)
    mo.acquire_storm_object(identityaccessrequest.receivertip.internaltip.context)
    iar["submission_context"] = mo.dump_localized_key('name', language)

    return iar


@transact_ro
def get_identityaccessrequest_list(store, language):
    return [serialize_identityaccessrequest(iar, language)
        for iar in store.find(IdentityAccessRequest, IdentityAccessRequest.reply == u'pending')]


@transact_ro
def get_identityaccessrequest(store, identityaccessrequest_id, language):
    iar = store.find(IdentityAccessRequest,
                     IdentityAccessRequest.id == identityaccessrequest_id).one()
    return serialize_identityaccessrequest(iar, language)


@transact
def update_identityaccessrequest(store, user_id, identityaccessrequest_id, request, language):
    iar = store.find(IdentityAccessRequest, IdentityAccessRequest.id == identityaccessrequest_id).one()

    if iar.reply == 'pending':
        iar.reply_date = datetime_now()
        iar.reply_user_id = user_id
        iar.reply = request['reply']
        if iar.reply == 'authorized':
            iar.receivertip.can_access_whistleblower_identity = True
        iar.reply_motivation = request['reply_motivation']

    return serialize_identityaccessrequest(iar, language)


class IdentityAccessRequestInstance(BaseHandler):
    """
    This handler allow custodians to manage an identity access request by a receiver
    """
    @transport_security_check('custodian')
    @authenticated('custodian')
    @inlineCallbacks
    def get(self, identityaccessrequest_id):
        """
        Parameters: the id of the identity access request
        Response: IdentityAccessRequestDesc
        Errors: IdentityAccessRequestIdNotFound, InvalidInputFormat, InvalidAuthentication
        """
        identityaccessrequest = yield get_identityaccessrequest(identityaccessrequest_id,
                                                                self.request.language)

        self.set_status(200)
        self.finish(identityaccessrequest)


    @transport_security_check('custodian')
    @authenticated('custodian')
    @inlineCallbacks
    def put(self, identityaccessrequest_id):
        """
        Parameters: the id of the identity access request
        Request: IdentityAccessRequestDesc
        Response: IdentityAccessRequestDesc
        Errors: IdentityAccessRequestIdNotFound, InvalidInputFormat, InvalidAuthentication
        """
        request = self.validate_message(self.request.body, requests.CustodianIdentityAccessRequestDesc)

        identityaccessrequest = yield update_identityaccessrequest(self.current_user.user_id,
                                                                   identityaccessrequest_id,
                                                                   request,
                                                                   self.request.language)

        self.set_status(200)
        self.finish(identityaccessrequest)


class IdentityAccessRequestsCollection(BaseHandler):
    """
    This interface return the list of the requests of access to whislteblower identities
    GET /identityrequests
    """

    @transport_security_check('custodian')
    @authenticated('custodian')
    @inlineCallbacks
    def get(self):
        """
        Response: identityaccessrequestsList
        Errors: InvalidAuthentication
        """
        answer = yield get_identityaccessrequest_list(self.request.language)

        self.set_status(200)
        self.finish(answer)
