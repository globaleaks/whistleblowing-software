# -*- coding: UTF-8
#   tip
#   ***
#
#   Contains all the logic for handling tip related operations, handled and
#   executed with /tip/* URI PATH interaction.

from twisted.internet.defer import inlineCallbacks
from cyclone.web import asynchronous

from globaleaks.handlers.base import BaseHandler
from globaleaks.models.externaltip import Comment, ReceiverTip, WhistleblowerTip,\
    TipGusNotFoundError, TipReceiptNotFoundError, TipPertinenceExpressed
from globaleaks.utils import log
from globaleaks.rest import base

import json

def is_receiver_token(tip_token):
    """
    @param tip_token: the received string from /tip/$whatever
    @return: True if is a tip_gus format, false if is not
    """

    try:
        retcheck = base.tipGUS().validate(tip_token)
    except:
        retcheck = True

    return not retcheck

class TipManagement(BaseHandler):
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
    def get(self, tip_token, *args):
        """
        Parameters: None
        Response: actorsTipDesc
        Errors: InvalidTipAuthToken
        """

        log.debug("[D] %s %s " % (__file__, __name__), "Class TipManagement", "get", "tip_token", tip_token)

        # tip_token can be: a tip_gus for a receiver, or a WhistleBlower receipt, understand
        # the format, help in addressing which kind of Tip need to be handled.

        comment_iface = Comment()
        # folder_iface = Folder()

        if is_receiver_token(tip_token):

            requested_t = ReceiverTip()

            try:
                tip_description = yield requested_t.receiver_get_single(tip_token)
                comment_list = yield comment_iface.get_comment_related(tip_description['tip_info']['internaltip_id'])

                self.set_status(200)
                self.write({'tip' : tip_description, 'comments' : comment_list})

            except TipGusNotFoundError, e:
                self.set_status(e.http_status)
                self.write({'error_message' : e.error_message, 'error_code' : e.error_code})

        else:

            requested_t = WhistleblowerTip()

            try:
                tip_description = yield requested_t.whistleblower_get_single(tip_token)
                comment_list = yield comment_iface.get_comment_related(tip_description['tip_info']['internaltip_id'])

                self.set_status(200)
                self.write({'tip' : tip_description, 'comments' : comment_list})

            except TipReceiptNotFoundError, e:
                self.set_status(e.http_status)
                self.write({'error_message' : e.error_message, 'error_code' : e.error_code})

        self.finish()

    @asynchronous
    @inlineCallbacks
    def post(self, tip_token, *arg, **kw):
        """
        Request: actorsTipDesc
        Response: actorsTipDesc
        Errors: InvalidTipAuthToken, InvalidInputFormat
        """

        log.debug("[D] %s %s " % (__file__, __name__), "Class TipRoot", "post", "tip_token", tip_token)

        request = json.loads(self.request.body)

        if not request:
            # this need a dedicated entry in error dict
            self.set_status(408)
            self.write({'error_message' : 'expected messages in POST', 'error_code' : 123})

        elif is_receiver_token(tip_token):

            requested_t = ReceiverTip()

            try:
                if request['total_delete']:
                    yield requested_t.total_delete(tip_token)
                elif request['personal_delete']:
                    yield requested_t.personal_delete(tip_token)
                elif request['is_pertinent']:
                    yield requested_t.pertinence_vote(tip_token, request['is_pertinent'])

                self.set_status(200)

            except TipGusNotFoundError, e:
                self.set_status(e.http_status)
                self.write({'error_message' : e.error_message, 'error_code' : e.error_code})

            except TipPertinenceExpressed, e:
                self.set_status(e.http_status)
                self.write({'error_message' : e.error_message, 'error_code' : e.error_code})

            # TODO, error handling for lacking of total_delete privileges

        else:
            # this need a dedicated entry in error dict
            self.set_status(410)
            self.write({'error_message' : 'receiver Tip not used', 'error_code' : 123})

        self.finish()


class TipsAvailable(BaseHandler):
    """
    T2
    This interface return the summary list of the Tips available for the authenticated Receiver
    GET /tips/<receiver_tip_GUS>/
    """

    @asynchronous
    @inlineCallbacks
    def get(self, tip_token):
        """
        Parameters: None
        Response: receiverTipsList
        Errors: InvalidTipAuthToken
        """
        pass


# FULLY REVIEW TODO
class TipCommentManagement(BaseHandler):
    """
    T3
    Interface use to read/write comments inside of a Tip, is not implemented as CRUD because we've not
    needs, at the moment, to delete/update comments once has been published. Comments is intended, now,
    as a stone written consideration about Tip reliability, therefore no editing and rethinking is
    permitted.
    """

    @asynchronous
    @inlineCallbacks
    def get(self, tip_token, *uriargs):
        """
        Parameters: None (TODO start/end)
        Response: actorsCommentList
        Errors: InvalidTipAuthToken
        """
        pass

    @asynchronous
    @inlineCallbacks
    def post(self, tip_token, *uriargs):
        """
        Request: actorsCommentDesc
        Response: actorsCommentDesc
        Errors: InvalidTipAuthToken, InvalidInputFormat
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class TipComment", "post", tip_token)

        request = json.loads(self.request.body)

        # this is not yet the
        if not 'comment' in request:
            self.set_status(406)
        elif not request['comment']:
            self.set_status(406)
        else:
            comment_iface = Comment()

            try:

                if is_receiver_token(tip_token):
                    receivert_iface = ReceiverTip()
                    tip_description = yield receivert_iface.admin_get_single(tip_token)
                    yield comment_iface.add_comment(tip_description['internaltip_id'], request['comment'], u"receiver", tip_description['receiver_name'])
                    # TODO: internaltip <> last_usage_time_update()

                else:
                    wbt_iface = WhistleblowerTip()
                    tip_description = yield wbt_iface.admin_get_single(tip_token)
                    yield comment_iface.add_comment(tip_description['internaltip_id'], request['comment'], u"whistleblower")
                    # TODO: internaltip <> last_usage_time_update()

                self.set_status(200)

            except TipGusNotFoundError, e:
                self.set_status(e.http_status)
                self.write({'error_message' : e.error_message, 'error_code' : e.error_code})

        self.finish()


