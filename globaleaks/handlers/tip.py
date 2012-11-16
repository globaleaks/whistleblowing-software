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
from globaleaks.models.externaltip import ReceiverTip, WhistleblowerTip,\
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

    @asynchronous
    @inlineCallbacks
    def get(self, tip_token):
        log.debug("[D] %s %s " % (__file__, __name__), "Class TipRoot", "get", "tip_token", tip_token)

        # tip_token can be: a tip_gus for a receiver, or a WhistleBlower receipt, understand
        # the format, help in addrressing which kind of Tip need to be handled.

        if is_receiver_token(tip_token):

            requested_t = ReceiverTip()

            try:
                tip_description = yield requested_t.receiver_get_single(tip_token)
                self.set_status(200)
                self.write(tip_description)

            except TipGusNotFoundError, e:
                self.set_status(e.http_status)
                self.write({'error_message' : e.error_message, 'error_code' : e.error_code})

        else:

            requested_t = WhistleblowerTip()

            try:
                tip_description = yield requested_t.whistleblower_get_single(tip_token)
                self.set_status(200)
                self.write(tip_description)

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

    log.debug("[D] %s %s " % (__file__, __name__), "Class TipComment", "BaseHandler", BaseHandler)

    @asynchronous
    @inlineCallbacks
    def post(self, receipt):
        log.debug("[D] %s %s " % (__file__, __name__), "Class TipComment", "post", receipt)
        print "New comment in %s" % receipt
        request = json.loads(self.request.body)

        if 'comment' in request and request['comment']:
            tip = ReceiverTip()
            # REMIND - spòlit between receiver and wb, because you need to
            # know derivated tip infos.
            yield tip.add_comment(receipt, request['comment'])

            self.set_status(200)
        else:
            self.set_status(404)

        self.finish()

class TipFiles(BaseHandler):
    """
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
    log.debug("[D] %s %s " % (__file__, __name__), "Class TipFinalize", "BaseHandler", BaseHandler)

    def post(self, *arg, **kw):
        log.debug("[D] %s %s " % (__file__, __name__), "Class TipFinalize", "post")
        pass


class TipDownload(BaseHandler):
    """
    Receiver only - enabled only if local delivery is set
    """
    log.debug("[D] %s %s " % (__file__, __name__), "Class TipDownload", "BaseHandler", BaseHandler)

    def get(self, *arg, **kw):
        log.debug("[D] %s %s " % (__file__, __name__), "Class TipDownload", "get")
        pass

class TipPertinence(BaseHandler):
    """
    pertinence is marked as GET, but need to be a POST,
    either because a receiver may express +1 -1 values,
    and because can be extended in the future
    """
    log.debug("[D] %s %s " % (__file__, __name__), "Class TipPertinence", "BaseHandler", BaseHandler)

    def post(self, *arg, **kw):
        log.debug("[D] %s %s " % (__file__, __name__), "Class TipPertinence", "post")
        pass

