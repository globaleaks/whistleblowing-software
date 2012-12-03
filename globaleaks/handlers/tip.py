# -*- coding: UTF-8
#   tip
#   ***
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
#   Contains all the logic for handling tip related operations.

from twisted.internet.defer import inlineCallbacks
from cyclone.web import asynchronous

from globaleaks.handlers.base import BaseHandler
from globaleaks.models.externaltip import Comment, ReceiverTip, WhistleblowerTip,\
    TipGusNotFoundError, TipReceiptNotFoundError, TipPertinenceExpressed
from globaleaks.utils import log
import globaleaks.messages.base
import json

def is_receiver_token(tip_token):
    """
    @param tip_token: the received string from /tip/$whatever
    @return: True if is a tip_gus format, false if is not
    """

    try:
        retcheck = globaleaks.messages.base.tipGUS().validate(tip_token)
    except:
        retcheck = True

    return not retcheck

class TipRoot(BaseHandler):
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
    """

    @asynchronous
    @inlineCallbacks
    def get(self, tip_token):
        log.debug("[D] %s %s " % (__file__, __name__), "Class TipRoot", "get", "tip_token", tip_token)

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
        root of /tip/ POST manage delete, forwarding and pertinence options.
        Only the receiver may have this properties.
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


class TipComment(BaseHandler):
    """
    T2
    Interface use to read/write comments inside of a Tip
    """

    @asynchronous
    @inlineCallbacks
    def post(self, tip_token):
        """
        /tip/$tip/comment
        *Request
            {
            'comment' : 'tha shit'
            }
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


class TipFiles(BaseHandler):
    """
    T3
    files CURD at the moment is not yet finished
    along with the javascript part.
    """
    log.debug("[D] %s %s " % (__file__, __name__), "Class TipFiles", "BaseHandler", BaseHandler)
    def get(self, *arg, **kw):
        log.debug("[D] %s %s " % (__file__, __name__), "Class TipFiles", "get")
        pass

    def put(self, *arg, **kw):
        log.debug("[D] %s %s " % (__file__, __name__), "Class TipFiles", "put")
        pass

    def post(self, *arg, **kw):
        log.debug("[D] %s %s " % (__file__, __name__), "Class TipFiles", "post")
        pass

    def delete(self, *arg, **kw):
        log.debug("[D] %s %s " % (__file__, __name__), "Class TipFiles", "delete")
        pass

class TipFinalize(BaseHandler):
    """
    T4
    This interface aim to close the file uploading - need to be removed in the next (and last) API refactor
    """
    log.debug("[D] %s %s " % (__file__, __name__), "Class TipFinalize", "BaseHandler", BaseHandler)

    def post(self, *arg, **kw):
        log.debug("[D] %s %s " % (__file__, __name__), "Class TipFinalize", "post")
        pass


class TipDownload(BaseHandler):
    """
    T5
    Receiver only - enabled only if local delivery is set - not yet implemented nor documented
    """
    log.debug("[D] %s %s " % (__file__, __name__), "Class TipDownload", "BaseHandler", BaseHandler)

    def get(self, *arg, **kw):
        log.debug("[D] %s %s " % (__file__, __name__), "Class TipDownload", "get")
        pass

