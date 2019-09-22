# -*- coding: utf-8
from io import BytesIO as StringIO

from twisted.logger import ILogObserver, Logger
from twisted.python import log
from twisted.web.http import Request

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

Request._log = Logger(observer=NullObserver())
Request.gotLength = mock_Request_gotLength
