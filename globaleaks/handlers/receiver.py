# -*- coding: UTF-8
#   receiver
#   ********
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
from globaleaks.rest import answers
from globaleaks.utils import log

from globaleaks.handlers import base

class ReceiverRoot(base.BaseHandler):
    """
    We should implement here all the operations that are related to the
    receiver.
    All the top level handlers should go here, all the more "advanced" logic
    should go in a separate object that is under the receiver namespace (i.e.
    it should be inside of the globaleaks/receiver/ directory)
    """

    log.debug("[D] %s %s " % (__file__, __name__), "Class ReceiverRoot", "base.BaseHandler", base.BaseHandler)

    # remind, for be auth here need a tip_gus and a receiver_gus, a Receiver.secret if secret if supported
    # R1
    def get(self):
        log.debug("[D] %s %s " % (__file__, __name__), "Class ReceiverRoot", "base.BaseHandler", base.BaseHandler)
        pass

class ReceiverModule(base.BaseHandler):
    # R2
    def get(self):
        pass

    def post(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass
