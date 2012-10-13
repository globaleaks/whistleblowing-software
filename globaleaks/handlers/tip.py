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

class TipRoot(BaseHandler):

    @asynchronous
    @inlineCallbacks
    def get(self, receipt):
        print "Processing %s" % receipt
        tip = Tip()
        tip_dict = yield tip.lookup(receipt)
        self.write(tip_dict)
        self.finish()

    """
    root of /tip/ POST handle *deleting* and *forwarding* options,
    they are checked in the tip-properties
    (assigned by the tip propetary)
    """
    def post(self, *arg, **kw):
        pass

class TipComment(BaseHandler):
    def post(self, *arg, **kw):
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

