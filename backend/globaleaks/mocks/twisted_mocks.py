# -*- coding: utf-8
from io import BytesIO as StringIO

from pkg_resources import parse_version

from twisted import __version__
from twisted.internet import defer
from twisted.python import log
from twisted.web.client import HTTPPageGetter
from twisted.web.http import HTTPChannel, HTTPFactory, Request


# Mocks applied to every twisted version
def mock_log(*args, **kw):
    pass


def mock_Request_gotLength(self, length):
    self.content = StringIO()

log.msg = log.err = mock_log
Request.gotLength = mock_Request_gotLength


def mock_HTTPChannel__timeoutConnection(self):
    """
    This mock is required to just comment a log line and apply patch fix introduced in Twisted 17.1.0
    https://github.com/twisted/twisted/commit/5f37cd1b83a2609f23a9dab46fd023cc941153f2
    """
    self.transport.loseConnection()


# Mocks applied to versions of twisted < 17.0.1
if parse_version(__version__) <= parse_version('17.1.0'):
    HTTPFactory__init__orig = HTTPFactory.__init__

    def mock_HTTPFactory__init__(self, logPath=None, timeout=60, logFormatter=None):
        """
        The mock is required to fix tx bug #3746 with the patch introduced in Twisted 17.1.0
        timeout is set to 60 instead of 60 * 60 * 12.
        """
        HTTPFactory__init__orig(self, logPath, timeout, logFormatter)

    HTTPFactory.__init__ = mock_HTTPFactory__init__
    HTTPChannel.timeoutConnection = mock_HTTPChannel__timeoutConnection

# Mocks applied to versions of twisted < 16.2.0
if parse_version(__version__) <= parse_version('16.2.0'):
    def mock_HTTPPageGetter_timeout(self, data):
        """
        This mock is required to fix tx bug #8318 with patch introduced in 16.2.0
        self.transport.abortConnection() is used in place of self.transport.loseConnection()
        """
        def timeout(self):
            self.quietLoss = True
            self.transport.abortConnection()
            self.factory.noPage(defer.TimeoutError("Getting %s took longer than %s seconds." % (self.factory.url, self.factory.timeout)))

        HTTPPageGetter.timeout = mock_HTTPPageGetter_timeout
