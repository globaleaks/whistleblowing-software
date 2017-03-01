# -*- coding: UTF-8

import os
from twisted.internet import defer
from twisted.web.client import HTTPPageGetter
from twisted.web.http import combinedLogFormatter, HTTPFactory

HTTPFactory__init__orig = HTTPFactory.__init__

def mock_HTTPFactory__init__(self, logPath=None, timeout=60, logFormatter=None):
    """
    The mock is required to fix tx bug #3746 with the patch introduced in Twisted 17.1.0
    timeout is set to 60 instead of 60 * 60 * 12. 
    """
    HTTPFactory__init__orig(self, logPath=None, timeout=60, logFormatter=None)


def mock_HTTPPageGetter_timeout(self, data):
    """
    This mock is required to fix tx bug #8318 with patch introduced in 16.2.0
    self.transport.loseConnection() is used in place of self.transport.loseConnection()
    """
    def timeout(self):
        self.quietLoss = True
        self.transport.loseConnection()
        self.factory.noPage(defer.TimeoutError("Getting %s took longer than %s seconds." % (self.factory.url, self.factory.timeout)))


HTTPPageGetter.timeout = mock_HTTPPageGetter_timeout
HTTPFactory.__init__ = mock_HTTPFactory__init__
