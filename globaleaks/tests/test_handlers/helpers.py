import json

from twisted.trial import unittest
from twisted.test import proto_helpers
from storm.twisted.testing import FakeThreadPool
from storm.twisted.transact import Transactor
from storm.zope.zstorm import ZStorm
from cyclone.util import ObjectDict as OD
from cyclone import httpserver
from cyclone.web import Application


from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers import authentication
from globaleaks.rest import errors
from globaleaks.config import config


class TestHandler(unittest.TestCase):
    """
    :attr _handler: handler class to be tested
    """
    _handler = None

    def setUp(self):
        """
        override default handlers' get_store with a mock store used for testing/
        """
        database_uri = 'sqlite:///test.db'
        zstorm = ZStorm()
        zstorm.set_default_uri('test_store', database_uri)
        threadpool = FakeThreadPool()
        transactor = Transactor(threadpool)

        @classmethod
        def get_mock_store(cls):
            return  zstorm.get('test_store')

        #override handle's get_store and transactor
        BaseHandler.get_store = get_mock_store
        BaseHandler.transactor = transactor

    def tearDown(self):
        """
        Clear the actual transport.
        """
        self.tr = None

    def request(self, jbody=None, headers=None, body='', remote_ip='0.0.0.0', method='MOCK'):
        """
        :param method: HTTP method, e.g. "GET" or "POST"
        :param uri: URL to fetch
        :param headers: (dict or :class:`cyclone.httputil.HTTPHeaders` instance) HTTP headers to pass on the request
        :param body:
        :param jbody:
        :param remote_ip:
        """
        if jbody and not body:
            body = json.dumps(jbody)
        elif body and jbody:
            raise ValueErorr('jbody and body in conflict')

        application = Application([])
        self.tr = proto_helpers.StringTransport()
        connection = httpserver.HTTPConnection()
        connection.factory = application
        connection.makeConnection(self.tr)

        request = httpserver.HTTPRequest(uri='mock',
                                         method=method,
                                         headers=headers,
                                         body=body,
                                         remote_ip=remote_ip,
                                         connection=connection)
        return self._handler(application, request)
