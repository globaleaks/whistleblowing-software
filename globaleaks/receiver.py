# -*- coding: UTF-8
#   receiver
#   ********
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
from globaleaks import DummyHandler
class Receiver(DummyHandler):
    """
    XXX

    this is an "Handler".
    do only implement the REST I/O, or all the operation of the Receiver ?
    """

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

