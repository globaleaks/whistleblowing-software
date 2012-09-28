# -*- coding: UTF-8
#   tip
#   ***
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
#   Contains all the logic for handling tip related operations.

from globaleaks import Processor
from globaleaks.utils import recurringtypes as GLT
from globaleaks.utils import dummy

class Tip(Processor):

    def root_GET(self, *arg, **kw):

        ret = GLT.tipDetailsDict()

        dummy.TIP_ROOT_GET(ret)

        return ret.unroll()

    """
    root of /tip/ POST handle *deleting* and *forwarding* options,
    they are checked in the tip-properties 
    (assigned by the tip propetary)
    """
    def root_POST(self, *arg, **kw):
        return self.root_GET(arg, kw)

    def comment_POST(self, *arg, **kw):
        # set return code to 200 
        return None


    """
    files CURD at the moment is not yet finished
    along with the javascript part.
    """
    def files_GET(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

    def files_PUT(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

    def files_POST(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

    def files_DELETE(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}


    def finalize_POST(self, *arg, **kw):
        # set return code to 200 
        return None

    """
    Receiver only - enabled only if local delivery is set
    """
    def download_GET(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

    """
    pertinence is marked as GET, but need to be a POST,
    either because a receiver may express +1 -1 values,
    and because can be extended in the future
    """
    def pertinence_POST(self, *arg, **kw):
        # set return code to 200 
        return None

