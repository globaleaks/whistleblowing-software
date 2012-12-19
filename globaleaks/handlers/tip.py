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
from globaleaks.models.externaltip import Comment, ReceiverTip, WhistleblowerTip
from globaleaks.models.internaltip import InternalTip
from globaleaks.rest.base import validateMessage
from globaleaks.rest import requests, base
from globaleaks.rest.errors import InvalidTipAuthToken, InvalidInputFormat, ForbiddenOperation, TipGusNotFound, TipReceiptNotFound, TipPertinenceExpressed
import json

# XXX need to be updated along the receipt hashing and format
def is_receiver_token(tip_token):
    """
    @param tip_token: the received string from /tip/$whatever
    @return: True if is a tip_gus format, false if is not
    """

    if len(tip_token) == 52 and tip_token[0] == 't' and tip_token[1] == '_':
        return True
    else:
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

    @asynchronous
    @inlineCallbacks
    def get(self, tip_token, *uriargs):
        """
        Parameters: None
        Response: actorsTipDesc
        Errors: InvalidTipAuthToken

        tip_token can be: a tip_gus for a receiver, or a WhistleBlower receipt, understand
        the format, help in addressing which kind of Tip need to be handled.
        """

        # file_iface = File()

        try:
            if is_receiver_token(tip_token):
                print "I'm a receiver with %s" % tip_token
                requested_t = ReceiverTip()
                tip_description = yield requested_t.receiver_get_single(tip_token)
            else:
                print "I'm a whistleblower with %s" % tip_token
                requested_t = WhistleblowerTip()
                tip_description = yield requested_t.whistleblower_get_single(tip_token)

            tip_description.pop('receiver_map')
            # need to be provided by input filtering
            self.set_status(200)
            self.write(json.dumps(tip_description))

        except TipGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message' : e.error_message, 'error_code' : e.error_code})

        except TipReceiptNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message' : e.error_message, 'error_code' : e.error_code})

        self.finish()

    @asynchronous
    @inlineCallbacks
    def put(self, tip_token, *uriargs):
        """
        Request: actorsTipOpsDesc
        Response: actorsTipDesc
        Errors: InvalidTipAuthToken, InvalidInputFormat, ForbiddenOperation

        This interface modify some tip status value. pertinence, personal delete are handled here.
        Total delete operation is handled in this class, by the DELETE HTTP method.
        Those operations (may) trigger a 'system comment' inside of the Tip comment list.
        """

        try:
            request = validateMessage(self.request.body, requests.actorsTipOpsDesc)

            if not is_receiver_token(tip_token):
                raise ForbiddenOperation

            requested_t = ReceiverTip()

            if request['personal_delete']:
                yield requested_t.personal_delete(tip_token)
            if request['is_pertinent']:
                yield requested_t.pertinence_vote(tip_token, request['is_pertinent'])

            self.set_status(200)

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.write({'error_message' : e.error_message, 'error_code' : e.error_code})

        except ForbiddenOperation, e:

            self.set_status(e.http_status)
            self.write({'error_message' : e.error_message, 'error_code' : e.error_code})

        except TipGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message' : e.error_message, 'error_code' : e.error_code})

        except TipPertinenceExpressed, e:

            self.set_status(e.http_status)
            self.write({'error_message' : e.error_message, 'error_code' : e.error_code})

        else:
            # this need a dedicated entry in error dict
            self.set_status(410)
            self.write({'error_message' : 'receiver Tip not used', 'error_code' : 123})

        self.finish()


    @asynchronous
    @inlineCallbacks
    def delete(self, tip_token, *uriargs):
        """
        Request: None
        Response: None
        Errors: ForbiddenOperation

        When an uber-receiver decide to "total delete" a Tip, is handled by this call.
        """
        try:

            if not is_receiver_token(tip_token):
                raise ForbiddenOperation

            requested_t = ReceiverTip()
            yield requested_t.total_delete(tip_token)

            self.set_status(200)

        except ForbiddenOperation, e:

            self.set_status(e.http_status)
            self.write({'error_message' : e.error_message, 'error_code' : e.error_code})



class TipCommentCollection(BaseHandler):
    """
    T2
    Interface use to read/write comments inside of a Tip, is not implemented as CRUD because we've not
    needs, at the moment, to delete/update comments once has been published. Comments is intended, now,
    as a stone written consideration about Tip reliability, therefore no editing and rethinking is
    permitted.
    """

    @asynchronous
    @inlineCallbacks
    def get(self, tip_token, *uriargs):
        """
        Parameters: None (TODO start/end, date)
        Response: actorsCommentList
        Errors: InvalidTipAuthToken
        """

        try:

            if is_receiver_token(tip_token):
                print "Comment: I'm a receiver with %s" % tip_token
                requested_t = ReceiverTip()
                tip_description = yield requested_t.receiver_get_single(tip_token)
            else:
                print "Comment: I'm a whistleblower with %s" % tip_token
                requested_t = WhistleblowerTip()
                tip_description = yield requested_t.whistleblower_get_single(tip_token)

            comment_iface = Comment()
            comment_list = yield comment_iface.get_comment_related(tip_description['internaltip_id'])

            self.set_status(200)
            self.write(json.dumps(comment_list))

        except TipGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message' : e.error_message, 'error_code' : e.error_code})

        except TipReceiptNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message' : e.error_message, 'error_code' : e.error_code})

        self.finish()

    @asynchronous
    @inlineCallbacks
    def post(self, tip_token, *uriargs):
        """
        Request: actorsCommentDesc
        Response: actorsCommentDesc
        Errors: InvalidTipAuthToken, InvalidInputFormat, TipGusNotFound, TipReceiptNotFound
        """

        comment_iface = Comment()

        try:
            request = validateMessage(self.request.body, requests.actorsCommentDesc)

            if is_receiver_token(tip_token):

                print "Comment: I'm a receiver with %s" % tip_token
                requested_t = ReceiverTip()

                tip_description = yield requested_t.admin_get_single(tip_token)
                comment_stored = yield comment_iface.add_comment(tip_description['internaltip_id'],
                    request['content'], u"receiver", tip_description['receiver_gus'])

            else:
                print "Comment: I'm a whistleblower with %s" % tip_token
                requested_t = WhistleblowerTip()

                tip_description = yield requested_t.admin_get_single(tip_token)
                comment_stored = yield comment_iface.add_comment(tip_description['internaltip_id'],
                    request['content'], u"whistleblower")

            # TODO: internaltip <> last_usage_time_update()
            self.set_status(200)
            self.write(json.dumps(comment_stored))

        except TipGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message' : e.error_message, 'error_code' : e.error_code})

        except TipReceiptNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message' : e.error_message, 'error_code' : e.error_code})

        self.finish()



class TipReceiversCollection(BaseHandler):
    """
    T3
    This interface return the list of the Receiver active in a Tip.
    GET /tip/<auth_tip_token>/receivers
    """

    @asynchronous
    @inlineCallbacks
    def get(self, tip_token, *uriargs):
        """
        Parameters: None
        Response: actorsReceiverList
        Errors: InvalidTipAuthToken
        """

        try:
            if is_receiver_token(tip_token):

                print "Receiver: I'm a receiver with %s" % tip_token
                requested_t = ReceiverTip()
                tip_description = yield requested_t.admin_get_single(tip_token)

            else:

                print "Receiver: I'm a whistleblower with %s" % tip_token
                requested_t = WhistleblowerTip()
                tip_description = yield requested_t.admin_get_single(tip_token)

            itip_iface = InternalTip()

            inforet = yield itip_iface.get_receivers_map(tip_description['internaltip_id'])

            self.write(json.dumps(inforet))
            self.set_status(200)

        except TipGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message' : e.error_message, 'error_code' : e.error_code})

        except TipReceiptNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message' : e.error_message, 'error_code' : e.error_code})

        self.finish()



