# -*- coding: utf-8 -*-
import json

from globaleaks.handlers.staticfile import StaticFileHandler
from globaleaks.rest import errors
from globaleaks.settings import Settings
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks

FUTURE = 100


class TestStaticFileHandler(helpers.TestHandler):
    _handler = StaticFileHandler

    @inlineCallbacks
    def test_get_existent(self):
        handler = self.request(kwargs={'path': Settings.client_path})
        yield handler.get('')
        self.assertTrue(handler.request.getResponseBody().startswith('<!doctype html>'))

    @inlineCallbacks
    def test_get_unexistent(self):
        handler = self.request(kwargs={'path': Settings.client_path})

        try:
            yield handler.get('unexistent')
        except errors.ResourceNotFound:
            return

        self.fail('should throw resource not found error')
