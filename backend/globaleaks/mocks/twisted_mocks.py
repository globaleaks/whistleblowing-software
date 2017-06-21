# -*- coding: UTF-8
import json
import types
from io import BytesIO as StringIO

from twisted.internet import defer
from twisted.protocols import policies
from twisted.web import http
from twisted.web.client import HTTPPageGetter
from twisted.web.http import HTTPChannel, HTTPFactory, Request

from globaleaks.settings import GLSettings


HTTPFactory__init__orig = HTTPFactory.__init__
Request__write__orig = Request.write


def mock_Request_gotLength(self, length):
    self.content = StringIO()


def mock_HTTPFactory__init__(self, logPath=None, timeout=60, logFormatter=None):
    """
    The mock is required to fix tx bug #3746 with the patch introduced in Twisted 17.1.0
    timeout is set to 60 instead of 60 * 60 * 12.
    """
    HTTPFactory__init__orig(self, logPath, timeout, logFormatter)


def mock_HTTPPageGetter_timeout(self, data):
    """
    This mock is required to fix tx bug #8318 with patch introduced in 16.2.0
    self.transport.abortConnection() is used in place of self.transport.loseConnection()
    """
    def timeout(self):
        self.quietLoss = True
        self.transport.abortConnection()
        self.factory.noPage(defer.TimeoutError("Getting %s took longer than %s seconds." % (self.factory.url, self.factory.timeout)))


def mock_HTTChannel__timeoutConnection(self):
    """
    This mock is required to just comment a log line
    """
    # log.info("Timing out client: %s" % str(self.transport.getPeer()))
    policies.TimeoutMixin.timeoutConnection(self)


Request.gotLength = mock_Request_gotLength
HTTPPageGetter.timeout = mock_HTTPPageGetter_timeout
HTTPFactory.__init__ = mock_HTTPFactory__init__
HTTPChannel.timeoutConnection = mock_HTTChannel__timeoutConnection
