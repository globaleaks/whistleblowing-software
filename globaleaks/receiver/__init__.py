# -*- coding: UTF-8
#   receiver
#   ********
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
from globaleaks import DummyHandler
class Receiver(object):
    """
    XXX

    this is an "Handler".
    do only implement the REST I/O, or all the operation of the Receiver ?

    We should implement here all the operations that are related to the
    receiver.
    All the top level handlers should go here, all the more "advanced" logic
    should go in a separate object that is under the receiver namespace (i.e.
    it should be inside of the globaleaks/receiver/ directory)
    - Art.

    """
    supportedModules = []

    def main(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

    def module(self, *arg, **kw):
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

