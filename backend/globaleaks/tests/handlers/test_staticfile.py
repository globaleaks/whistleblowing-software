# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.staticfile import StaticFileHandler
from globaleaks.rest import errors
from globaleaks.tests import helpers


class TestStaticFileHandler(helpers.TestHandler):
    _handler = StaticFileHandler

    @inlineCallbacks
    def test_get_existent(self):
        handler = self.request()
        yield handler.get('')
        self.assertTrue(handler.request.getResponseBody().decode().startswith('<!doctype html>'))

    def test_get_unexistent(self):
        handler = self.request()

        return self.assertRaises(errors.ResourceNotFound, handler.get, 'unexistent')
