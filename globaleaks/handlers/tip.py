# -*- coding: UTF-8
#
#   tip
#   ***
#
#   Contains all the logic for handling tip related operations, handled and
#   executed with /tip/* URI PATH interaction.

from twisted.internet.defer import inlineCallbacks
from cyclone.web import asynchronous

from globaleaks.handlers.base import BaseHandler
from globaleaks.transactors.crudoperations import CrudOperations
from globaleaks.rest import requests
from globaleaks.rest.errors import InvalidTipAuthToken, InvalidInputFormat, ForbiddenOperation, \
    TipGusNotFound, TipReceiptNotFound, TipPertinenceExpressed

# XXX need to be updated along the receipt hashing and format
def is_receiver_token(tip_token):
    """
    @param tip_token: the received string from /tip/$whatever
    @return: True if is a tip_gus format, false if is not
    """

    if len(tip_token) == 52 and tip_token[0] == 't' and tip_token[1] == '_':
        print "processing tip_token as Receiver", tip_token
        return True
    else:
        print "processing tip_token as WhistleBlower", tip_token
        return False

class TipInstance(BaseHandler):
    """
    T1
    This interface expose the Tip.

    Tip is the safe area, created with an expiration time, where Receivers (and optionally)
    Whistleblower can discuss about the submission, comments, collaborative voting, forward,
    promote, and perform other operation in this closed environment.
    In the request is present an unique token, aim to authenticate the users accessing to the
    resource, and giving accountability in resource accesses.
    Some limitation in access, security extensions an special token can exists, implemented by
    the extensions plugins.

    /tip/<tip_token>/
    tip_token is either a receiver_tip_gus or a whistleblower auth token
    """

    @inlineCallbacks
    def get(self, tip_token, *uriargs):
        """
        Parameters: None
        Response: actorsTipDesc
        Errors: InvalidTipAuthToken

        tip_token can be: a tip_gus for a receiver, or a WhistleBlower receipt, understand
        the format, help in addressing which kind of Tip need to be handled.
        """

        if is_receiver_token(tip_token):
            answer = yield CrudOperations().get_tip_by_receiver(tip_token)
        else:
            answer = yield CrudOperations().get_tip_by_wb(tip_token)

        self.set_status(answer['code'])
        self.finish(answer['data'])

    @inlineCallbacks
    def put(self, tip_token, *uriargs):
        """
        Request: actorsTipOpsDesc
        Response: None
        Errors: InvalidTipAuthToken, InvalidInputFormat, ForbiddenOperation

        This interface modify some tip status value. pertinence, personal delete are handled here.
        Total delete operation is handled in this class, by the DELETE HTTP method.
        Those operations (may) trigger a 'system comment' inside of the Tip comment list.

        This interface return None, because may execute a delete operation. The client
        know which kind of operation has been requested. If a pertinence vote, would
        perform a refresh on get() API, if a delete, would bring the user in other places.
        """

        # Until whistleblowers has not right to perform Tip operations...
        if not is_receiver_token(tip_token):
            raise ForbiddenOperation

        request = self.validate_message(self.request.body, requests.actorsTipOpsDesc)
        answer = yield CrudOperations().update_tip_by_receiver(tip_token, request)

        self.set_status(answer['code'])

        if answer.has_key('data'):
            self.finish(answer['data'])
        else:
            self.finish()

    @inlineCallbacks
    def delete(self, tip_token, *uriargs):
        """
        Request: None
        Response: None
        Errors: ForbiddenOperation, TipGusNotFound

        When an uber-receiver decide to "total delete" a Tip, is handled by this call.
        """
        # This until WB can't Total delete the Tip!
        if not is_receiver_token(tip_token):
            raise ForbiddenOperation

        answer = yield CrudOperations().delete_tip(tip_token)

        self.set_status(answer['code'])
        self.finish()

class TipCommentCollection(BaseHandler):
    """
    T2
    Interface use to read/write comments inside of a Tip, is not implemented as CRUD because we've not
    needs, at the moment, to delete/update comments once has been published. Comments is intended, now,
    as a stone written consideration about Tip reliability, therefore no editing and rethinking is
    permitted.
    """

    @inlineCallbacks
    def get(self, tip_token, *uriargs):
        """
        Parameters: None (TODO start/end, date)
        Response: actorsCommentList
        Errors: InvalidTipAuthToken
        """

        if is_receiver_token(tip_token):
            answer = yield CrudOperations().get_comment_list_by_receiver(tip_token)
        else:
            answer = yield CrudOperations().get_comment_list_by_wb(tip_token)

        self.set_status(answer['code'])
        self.finish(answer['data'])

    @inlineCallbacks
    def post(self, tip_token, *uriargs):
        """
        Request: actorsCommentDesc
        Response: actorsCommentDesc
        Errors: InvalidTipAuthToken, InvalidInputFormat, TipGusNotFound, TipReceiptNotFound
        """

        request = self.validate_message(self.request.body, requests.actorsCommentDesc)

        if is_receiver_token(tip_token):
            answer = yield CrudOperations().new_comment_by_receiver(tip_token, request)
        else:
            answer = yield CrudOperations().new_comment_by_wb(tip_token, request)

        self.set_status(answer['code'])
        self.finish(answer['data'])

class TipReceiversCollection(BaseHandler):
    """
    T3
    This interface return the list of the Receiver active in a Tip.
    GET /tip/<auth_tip_token>/receivers
    """

    @inlineCallbacks
    def get(self, tip_token, *uriargs):
        """
        Parameters: None
        Response: actorsReceiverList
        Errors: InvalidTipAuthToken
        """

        if is_receiver_token(tip_token):
            answer = yield CrudOperations().get_receiver_list_by_receiver(tip_token)
        else:
            answer = yield CrudOperations().get_receiver_list_by_wb(tip_token)

        self.set_status(answer['code'])
        self.finish(answer['data'])

