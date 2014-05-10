# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

import json

from globaleaks.rest import requests
from globaleaks.tests import helpers
from globaleaks.handlers import node
from globaleaks.settings import GLSetting

class TestInfoCollection(helpers.TestHandler):
    _handler = node.InfoCollection

    @inlineCallbacks
    def test_get(self):
        handler = self.request({}, role='admin')
        yield handler.get()

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)
        self.assertEqual(len(self.responses[0]), 28)
        self._handler.validate_message(json.dumps(self.responses[0]), requests.anonNodeDesc)


class TestAhmiaDescriptionHandler(helpers.TestHandler):
    _handler = node.AhmiaDescriptionHandler

    @inlineCallbacks
    def test_get(self):
        handler = self.request({}, role='admin')
        yield handler.get()

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)
        self.assertEqual(len(self.responses[0]), 7)
        self._handler.validate_message(json.dumps(self.responses[0]), requests.ahmiaDesc)


class TestContextsCollection(helpers.TestHandler):
    _handler = node.ContextsCollection

    @inlineCallbacks
    def test_get(self):
        handler = self.request({}, role='admin')
        yield handler.get()

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)
        self.assertEqual(len(self.responses[0]), 1)
        self._handler.validate_message(json.dumps(self.responses[0]), requests.nodeContextCollection)


class TestReceiversCollection(helpers.TestHandler):
    _handler = node.ReceiversCollection

    @inlineCallbacks
    def test_get(self):
        handler = self.request({}, role='admin')
        yield handler.get()

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)
        self.assertEqual(len(self.responses[0]), 2)
        self._handler.validate_message(json.dumps(self.responses[0]), requests.nodeReceiverCollection)
