# -*- coding: UTF-8
#   receiver
#   ********
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
from globaleaks.rest import answers
from globaleaks.utils.dummy import dummy_answers as dummy

from globaleaks.handlers import base

class ReceiverRoot(base.BaseHandler):
    """
    We should implement here all the operations that are related to the
    receiver.
    All the top level handlers should go here, all the more "advanced" logic
    should go in a separate object that is under the receiver namespace (i.e.
    it should be inside of the globaleaks/receiver/ directory)
    """

    # R1
    def get(self, *arg, **kw):

        ret = answers.commonReceiverAnswer()

        dummy.RECEIVER_ROOT_GET(ret)

        return ret.unroll()

class ReceiverModule(base.BaseHandler):
    # R2
    def get(self, *arg, **kw):

        ret = answers.receiverModuleAnswer()

        dummy.RECEIVER_MODULE_GET(ret)

        return ret.unroll()

    def post(self, *arg, **kw):
        return self.get(*arg, **kw)

    def put(self, *arg, **kw):
        return self.get(*arg, **kw)

    def delete(self, *arg, **kw):
        return self.get(*arg, **kw)
