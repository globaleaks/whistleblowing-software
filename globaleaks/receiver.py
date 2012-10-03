# -*- coding: UTF-8
#   receiver
#   ********
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
from globaleaks import Processor
from globaleaks.rest import answers
from globaleaks.utils.dummy import dummy_answers as dummy


class Receiver(Processor):
    """
    We should implement here all the operations that are related to the
    receiver.
    All the top level handlers should go here, all the more "advanced" logic
    should go in a separate object that is under the receiver namespace (i.e.
    it should be inside of the globaleaks/receiver/ directory)
    """

    # R1
    def root_GET(self, *arg, **kw):

        ret = answers.commonReceiverAnswer()

        dummy.RECEIVER_ROOT_GET(ret)

        return ret.unroll()
 
    # R2
    def module_GET(self, *arg, **kw):

        ret = answers.receiverModuleAnswer()

        dummy.RECEIVER_MODULE_GET(ret)

        return ret.unroll()

    def module_POST(self, *arg, **kw):
        return self.module_GET(arg, kw)

    def module_PUT(self, *arg, **kw):
        return self.module_GET(arg, kw)

    def module_DELETE(self, *arg, **kw):
        return self.module_GET(arg, kw)
