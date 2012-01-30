import unittest

import tornado.httpserver
import tornado.httpclient
import tornado.ioloop

from globaleaks.www import app


class TestWWWWApp(unittest.TestCase):
    """
    Test the web application for GlobaLeaks.
    """

    port = 8888

    def setUp(self):
        """
        Set up a mock server.
        """
        self.server = tornado.httpserver.HTTPServer(app.application)
        self.client = tornado.httpclient.AsyncHTTPClient()

        self.server.listen(self.port)

    def tearDown(self):
        self.client.close()

    def urlfor(self, *page):
        """
        Construct an url using keywords given.
        """
        return 'http://localhost:%d/%s' % (self.port, '/'.join(page))

    def handle_request(self, message):
        """
        Callack for handling requests:
        save the message as class attribute, then close the socket.
        """
        self.response = message
        tornado.ioloop.IOLoop.instance().stop()

    def fetch(self, page, method='GET'):
        """
        Fetch an http page using self.client, then store the response to
        self.response.
        """
        self.client.fetch(self.urlfor(page), self.handle_request, method=method)
        tornado.ioloop.IOLoop.instance().start()

    def test_index(self):
        self.fetch('')

        self.assertEqual(self.response.code, 200)
        self.assertEqual(self.response.request.url, self.urlfor(''))

