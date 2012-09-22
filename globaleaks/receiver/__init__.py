# -*- coding: UTF-8
#   receiver
#   ********
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
from globaleaks import Processor

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
        print __file__,arg
        print __file__,kw
        return {'arg': arg, 'kw': kw}
 
    # R2
    def module_GET(self, *arg, **kw):
        print __file__,arg
        print __file__,kw
        return {'arg': arg, 'kw': kw}

    def module_POST(self, *arg, **kw):
        print __file__,arg
        print __file__,kw
        return {'arg': arg, 'kw': kw}

    def module_PUT(self, *arg, **kw):
        print __file__,arg
        print __file__,kw
        return {'arg': arg, 'kw': kw}

    def module_DELETE(self, *arg, **kw):
        print __file__,arg
        print __file__,kw
        return {'arg': arg, 'kw': kw}

    def import_fields(blah):
        """
        this function import the received JSON and make it fit in a
        receiverDict format.
        """
        pass

    def dummyDict(blah):
        """
        this function return a dummy moduleDict used during the test
        """
        pass
