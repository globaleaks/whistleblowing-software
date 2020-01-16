# -*- coding: utf-8
from io import BytesIO as StringIO

from twisted.logger import ILogObserver, Logger
from twisted.python import log
from twisted.web.http import HTTPChannel, Request

from zope.interface import implementer


@implementer(ILogObserver)
class NullObserver(object):
    def __call__(self, event):
        pass


# Mocks applied to every twisted version
def mock_log(*args, **kw):
    pass


def mock_Request_gotLength(self, length):
    self.content = StringIO()


log.msg = log.info = log.err = mock_log

null_logger = Logger(observer=NullObserver())

Request._log = null_logger
Request.gotLength = mock_Request_gotLength

HTTPChannel._log = null_logger

try:
    from twisted.web._http2 import H2Connection
except ImportError:
    pass
else:
    H2Connection._log = null_logger
