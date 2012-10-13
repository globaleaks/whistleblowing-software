# -*- coding: UTF-8
#   tip
#   ***
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
#   Contains all the logic for handling tip related operations.

from globaleaks import Processor
from globaleaks.rest import answers
from globaleaks.utils.dummy import dummy_answers as dummy

from globaleaks.handlers.base import BaseHandler

class TipRoot(BaseHandler):

    def get(self, *arg, **kw):

        ret = answers.tipDetailsDict()

        dummy.TIP_ROOT_GET(ret)

        return ret.unroll()

    """
    root of /tip/ POST handle *deleting* and *forwarding* options,
    they are checked in the tip-properties
    (assigned by the tip propetary)
    """
    def post(self, *arg, **kw):
        return self.root_GET(arg, kw)

class TipComment(BaseHandler):
    def post(self, *arg, **kw):
        # set return code to 200
        return None

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
        return {'arg': arg, 'kw': kw}

    def delete(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

class TipFinalize(BaseHandler):
    def post(self, *arg, **kw):
        # set return code to 200
        return None


class TipDownload(BaseHandler):
    """
    Receiver only - enabled only if local delivery is set
    """
    def get(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

class TipPertinence(BaseHandler):
    """
    pertinence is marked as GET, but need to be a POST,
    either because a receiver may express +1 -1 values,
    and because can be extended in the future
    """
    def post(self, *arg, **kw):
        # set return code to 200
        return None

