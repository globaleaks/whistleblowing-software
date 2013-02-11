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
from globaleaks import config
from globaleaks import db


_TEST_STORE = 'test_store'
def fillData():
    db.createTables()

class TestHandler(unittest.TestCase):
    """
    :attr _handler: handler class to be tested
    """
    _handler = None

    def setUp(self):
        """
        override default handlers' get_store with a mock store used for testing/
        """
        threadpool = FakeThreadPool()
        transactor = Transactor(threadpool)
        database_uri = 'test.db'

        self.messages = []
        @classmethod
        def mock_write(self, message):
            self.messages += message

        # override handle's get_store and transactor
        self._handler.write = mock_write
        self._handler.transactor = transactor
        config.config = config.Config(database_uri, _TEST_STORE)
        fillData()

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

        tr = proto_helpers.StringTransport()
        connection = httpserver.HTTPConnection()
        connection.factory = application
        connection.makeConnection(tr)

        request = httpserver.HTTPRequest(uri='mock',
                                         method=method,
                                         headers=headers,
                                         body=body,
                                         remote_ip=remote_ip,
                                         connection=connection)
        return self._handler(application, request)
