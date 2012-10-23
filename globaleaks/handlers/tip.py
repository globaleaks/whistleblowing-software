# -*- coding: UTF-8
#   tip
#   ***
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
#   Contains all the logic for handling tip related operations.

from twisted.internet.defer import inlineCallbacks
from cyclone.web import asynchronous, HTTPError

from globaleaks.handlers.base import BaseHandler
from globaleaks.models.tip import Tip, ReceiverTip
from globaleaks.utils import log
import json

class TipRoot(BaseHandler):

    log.debug("[D] %s %s " % (__file__, __name__), "Class TipRoot", "BaseHandler", BaseHandler)

    @asynchronous
    @inlineCallbacks
    def get(self, receipt):
        log.debug("[D] %s %s " % (__file__, __name__), "Class TipRoot", "get", "receipt", receipt)
        print "Processing %s" % receipt
        tip = Tip()

        tip_dict = yield tip.lookup(receipt)

        self.write(tip_dict)
        self.finish()


    """
    root of /tip/ POST handle *deleting* and *forwarding* options,
    they are checked in the tip-properties
    (assigned by the tip propetary), only the receiver may have
    this properties
    """
    def post(self, tip_gus, *arg, **kw):
        log.debug("[D] %s %s " % (__file__, __name__), "Class TipRoot", "post", "tip_gus", tip_gus)
        pass

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

