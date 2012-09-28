# -*- coding: UTF-8
#   receiver
#   ********
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
from globaleaks import Processor
from globaleaks.utils import recurringtypes as GLT
from globaleaks.utils import dummy

class commonReceiverAnswer(GLT.GLTypes):

    def __init__(self):

        GLT.GLTypes.__init__(self, self.__class__.__name__)

        self.define("tips", GLT.tipIndexDict() )
        self.define("receiver_properties", GLT.receiverDescriptionDict() )

        self.define_array("notification_method", GLT.moduleDataDict() , 1)
        self.define_array("delivery_method", GLT.moduleDataDict() , 1)

class receiverModuleAnswer(GLT.GLTypes):

    def __init__(self):
        GLT.GLTypes.__init__(self, self.__class__.__name__)
        self.define_array("modules", GLT.moduleDataDict() )


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

        ret = commonReceiverAnswer()

        dummy.RECEIVER_ROOT_GET(ret)

        return ret.unroll()
 
    # R2
    def module_GET(self, *arg, **kw):

        ret = receiverModuleAnswer()

        dummy.RECEIVER_MODULE_GET(ret)

        return ret.unroll()

    def module_POST(self, *arg, **kw):
        return self.module_GET(arg, kw)

    def module_PUT(self, *arg, **kw):
        return self.module_GET(arg, kw)

    def module_DELETE(self, *arg, **kw):
        return self.module_GET(arg, kw)
