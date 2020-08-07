# -*- coding: utf-8
from io import BytesIO as StringIO

from twisted.logger import ILogObserver, Logger
from twisted.python import log
from twisted.web.http import HTTPChannel, Request
from twisted.web._http2 import H2Connection

from zope.interface import implementer

def null_function(*args, **kw):
    pass

def mock_Request_gotLength(self, length):
    self.content = StringIO()

Request.gotLength = mock_Request_gotLength
Request.parseCookies = null_function

@implementer(ILogObserver)
class NullObserver(object):
    def __call__(self, event):
        pass


log.msg = log.info = log.err = null_function

null_logger = Logger(observer=NullObserver())
Request._log = null_logger
HTTPChannel._log = null_logger
H2Connection._log = null_logger
