# -*- coding: UTF-8
# receiver
# ********
#
# Implement the classes handling the requests performed to /receiver/* URI PATH
# Used by receivers to update personal preferences and access to personal data

from twisted.internet.defer import inlineCallbacks
from storm.expr import And, In

from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.handlers.base import BaseHandler
from globaleaks.models import IdentityAccessRequest
from globaleaks.rest import requests, errors
from globaleaks.rest.apicache import GLApiCache
from globaleaks.security import change_password
from globaleaks.settings import transact, transact_ro, GLSettings
from globaleaks.utils.utility import log, datetime_to_ISO8601, datetime_now


def serialize_identityaccessrequest(identityaccessrequest):
    iar_desc = dict({
        'id': identityaccessrequest.id,
        'receivertip_id': identityaccessrequest.receivertip_id,
        'request_date': datetime_to_ISO8601(identityaccessrequest.request_date),
        'request_user_id': identityaccessrequest.receivertip.receiver.id,
        'request_motivation': identityaccessrequest.request_motivation,
        'response_date': datetime_to_ISO8601(identityaccessrequest.request_date),
        'response_user_id': identityaccessrequest.response_user_id if identityaccessrequest.response_user_id is not None else '',
        'response': identityaccessrequest.response,
        'response_motivation': identityaccessrequest.response_motivation,
    })

    return iar_desc


@transact_ro
def get_identityaccessrequests_list(store):
    iars = store.find(IdentityAccessRequest)

    return [serialize_identityaccessrequest(iar) for iar in iars]


@transact_ro
def get_identityaccessrequest(store, identityaccessrequest_id):
    iar = store.find(IdentityAccessRequest, IdentityAccessRequest.id == identityaccessrequest_id).one()

    return serialize_identityaccessrequest(iar)


@transact
def update_identityaccessrequest(store, user_id, identityaccessrequest_id, request):
    iar = store.find(IdentityAccessRequest, IdentityAccessRequest.id == identityaccessrequest_id).one()

    iar.response_date = datetime_now()
    iar.response_user_id = user_id

    if iar.response == 'pending':
        iar.response = request['response']

    iar.response_motivation = request['response_motivation']

    return serialize_identityaccessrequest(iar)


class CustodianIdentityAccessRequestInstance(BaseHandler):
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
        identityaccessrequest = yield get_identityaccessrequest(identityaccessrequest_id)

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
                                                                   request)

        self.set_status(200)
        self.finish(identityaccessrequest)


class CustodianIdentityAccessRequestsCollection(BaseHandler):
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
        answer = yield get_identityaccessrequests_list()

        self.set_status(200)
        self.finish(answer)
