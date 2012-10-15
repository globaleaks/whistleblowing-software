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
from globaleaks.models.tip import Tip

class TipWbAccess(BaseHandler):
    """
    * This need to be defined in the API *
    actually we have TipRoot that is accessed with a receipt OR with an url-based auth.
    They need to be split. TipWbAccess would handle the receipt (or the WB auth method)
    and TipRoot would handle /tip/$tipid for receivers
    """

    @asynchronous
    @inlineCallbacks
    def post(self, receipt):
        print "Processing WB auth %s" % receipt
        tip = Tip()

        tip_dict = yield tip.wb_auth(receipt)

        self.write(tip_dict)
        self.finish()


class TipRoot(BaseHandler):

    @asynchronous
    @inlineCallbacks
    def get(self, tip_id):
        print "Processing WB auth %s" % receipt
        tip = Tip()

        tip_dict = yield tip.lookup(tip_id)

        self.write(tip_dict)
        self.finish()


    """
    root of /tip/ POST handle *deleting* and *forwarding* options,
    they are checked in the tip-properties
    (assigned by the tip propetary), only the receiver may have
    this properties
    """
    def post(self, tip_id, *arg, **kw):
        pass

class TipComment(BaseHandler):

    def post(self, tip_id, *arg, **kw):
        print "Processing %s" % tip_id

        pass

class TipFiles(BaseHandler):
    """
    files CURD at the moment is not yet finished
    along with the javascript part.
    """
    def get(self, *arg, **kw):
        pass

    def put(self, *arg, **kw):
        pass

    def post(self, *arg, **kw):
        pass

    def delete(self, *arg, **kw):
        pass

class TipFinalize(BaseHandler):
    def post(self, *arg, **kw):
        pass


class TipDownload(BaseHandler):
    """
    Receiver only - enabled only if local delivery is set
    """
    def get(self, *arg, **kw):
        pass

class TipPertinence(BaseHandler):
    """
    pertinence is marked as GET, but need to be a POST,
    either because a receiver may express +1 -1 values,
    and because can be extended in the future
    """
    def post(self, *arg, **kw):
        pass

