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
from globaleaks.utils.structures import Rosetta
from globaleaks.utils.utility import log, datetime_to_ISO8601, datetime_now


def serialize_identityaccessrequest(identityaccessrequest, language):
    iar = {
        'id': identityaccessrequest.id,
        'receivertip_id': identityaccessrequest.receivertip_id,
        'request_date': datetime_to_ISO8601(identityaccessrequest.request_date),
        'request_user_name': identityaccessrequest.receivertip.receiver.user.name,
        'request_motivation': identityaccessrequest.request_motivation,
        'response_date': datetime_to_ISO8601(identityaccessrequest.request_date),
        'response_user_name': identityaccessrequest.response_user.name \
            if identityaccessrequest.response_user is not None else '',
        'response': identityaccessrequest.response,
        'response_motivation': identityaccessrequest.response_motivation,
        'submission_date': datetime_to_ISO8601(identityaccessrequest.receivertip.internaltip.creation_date)
    }

    mo = Rosetta(identityaccessrequest.receivertip.internaltip.context.localized_strings)
    mo.acquire_storm_object(identityaccessrequest.receivertip.internaltip.context)
    iar["submission_context"] = mo.dump_localized_key('name', language)

    return iar


@transact_ro
def get_identityaccessrequests_list(store, language):
    return [serialize_identityaccessrequest(iar, language)
        for iar in store.find(IdentityAccessRequest)]


@transact_ro
def get_identityaccessrequest(store, identityaccessrequest_id, language):
    iar = store.find(IdentityAccessRequest, IdentityAccessRequest.id == identityaccessrequest_id).one()
    return serialize_identityaccessrequest(iar, language)


@transact
def update_identityaccessrequest(store, user_id, identityaccessrequest_id, request, language):
    iar = store.find(IdentityAccessRequest, IdentityAccessRequest.id == identityaccessrequest_id).one()

    iar.response_date = datetime_now()
    iar.response_user_id = user_id

    if iar.response == 'pending':
        iar.response = request['response']

    iar.response_motivation = request['response_motivation']

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
        answer = yield get_identityaccessrequests_list(self.request.language)

        self.set_status(200)
        self.finish(answer)
