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
from globaleaks.models.externaltip import Comment, ReceiverTip, WhistleblowerTip, File
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

        try:
            if is_receiver_token(tip_token):
                requested_t = ReceiverTip()
                tip_description = yield requested_t.get_single(tip_token)
            else:
                requested_t = WhistleblowerTip()
                tip_description = yield requested_t.get_single(tip_token)

            # TODO output filtering: actorsTipDesc
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
        Response: None
        Errors: InvalidTipAuthToken, InvalidInputFormat, ForbiddenOperation

        This interface modify some tip status value. pertinence, personal delete are handled here.
        Total delete operation is handled in this class, by the DELETE HTTP method.
        Those operations (may) trigger a 'system comment' inside of the Tip comment list.

        This interface return None, because may execute a delete operation. The client
        know which kind of operation has been requested. If a pertinence vote, would
        perform a refresh on get() API, if a delete, would bring the user in other places.
        """

        try:
            request = validateMessage(self.request.body, requests.actorsTipOpsDesc)

            if not is_receiver_token(tip_token):
                raise ForbiddenOperation

            receivertip_iface = ReceiverTip()

            if request['personal_delete']:
                yield receivertip_iface.personal_delete(tip_token)

            elif request['is_pertinent']:
                # elif is used to avoid the message with both delete+pertinence.
                # This operation is based in ReceiverTip and is returned
                # the sum of the vote expressed. This value is updated in InternalTip
                (itip_id, vote_sum) = yield receivertip_iface.pertinence_vote(tip_token, request['is_pertinent'])

                internaltip_iface = InternalTip()
                yield internaltip_iface.update_pertinence(itip_id, vote_sum)

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

        self.finish()


    @asynchronous
    @inlineCallbacks
    def delete(self, tip_token, *uriargs):
        """
        Request: None
        Response: None
        Errors: ForbiddenOperation, TipGusNotFound

        When an uber-receiver decide to "total delete" a Tip, is handled by this call.
        """
        try:

            if not is_receiver_token(tip_token):
                raise ForbiddenOperation

            receivertip_iface = ReceiverTip()

            receivers_map = yield receivertip_iface.get_receivers_by_tip(tip_token)

            if not receivers_map['actor']['can_delete_submission']:
                raise ForbiddenOperation

            # sibilings_tips has the keys: 'sibilings': [$] 'requested': $
            sibilings_tips = yield receivertip_iface.get_sibiligs_by_tip(tip_token)

            # delete all the related tip
            for sibiltip in sibilings_tips['sibilings']:
                yield receivertip_iface.personal_delete(sibiltip['tip_gus'])

            # and the tip of the called
            yield receivertip_iface.personal_delete(sibilings_tips['requested']['tip_gus'])

            # extract the internaltip_id, we need for the next operations
            itip_id = sibilings_tips['requested']['internaltip_id']

            file_iface = File()
            # remove all the files: XXX think if delivery method need to be inquired
            files_list = yield file_iface.get_files_by_itip(itip_id)
            print "TODO remove file_list", files_list

            comment_iface = Comment()
            # remove all the comments based on a specific itip_id
            comments_list = yield comment_iface.delete_comment_by_itip(itip_id)

            internaltip_iface = InternalTip()
            # finally, delete the internaltip
            internaltip_iface.tip_delete(sibilings_tips['requested']['internaltip_id'])

            self.set_status(200)

        except ForbiddenOperation, e:

            self.set_status(e.http_status)
            self.write({'error_message' : e.error_message, 'error_code' : e.error_code})

        except TipGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message' : e.error_message, 'error_code' : e.error_code})

        self.finish()


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
                requested_t = ReceiverTip()
                tip_description = yield requested_t.get_single(tip_token)
            else:
                requested_t = WhistleblowerTip()
                tip_description = yield requested_t.get_single(tip_token)

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

                requested_t = ReceiverTip()

                tip_description = yield requested_t.get_single(tip_token)
                comment_stored = yield comment_iface.add_comment(tip_description['internaltip_id'],
                    request['content'], u"receiver", tip_description['receiver_gus'])

            else:
                requested_t = WhistleblowerTip()

                tip_description = yield requested_t.get_single(tip_token)
                comment_stored = yield comment_iface.add_comment(tip_description['internaltip_id'],
                    request['content'], u"whistleblower")

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

                requested_t = ReceiverTip()
                tip_description = yield requested_t.get_single(tip_token)

            else:

                requested_t = WhistleblowerTip()
                tip_description = yield requested_t.get_single(tip_token)

            itip_iface = InternalTip()

            inforet = yield itip_iface.get_receivers_by_itip(tip_description['internaltip_id'])

            self.write(json.dumps(inforet))
            self.set_status(200)

        except TipGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message' : e.error_message, 'error_code' : e.error_code})

        except TipReceiptNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message' : e.error_message, 'error_code' : e.error_code})

        self.finish()



