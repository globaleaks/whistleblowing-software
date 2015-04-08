# -*- coding: utf-8 -*-
import json

from twisted.internet.defer import inlineCallbacks
from globaleaks.rest import requests
from globaleaks.tests import helpers
from globaleaks.handlers import node, admin


class TestNodeInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = node.NodeInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request({}, role='admin')
        yield handler.get()

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)
        self._handler.validate_message(json.dumps(self.responses[0]), requests.NodeDesc)


class TestAhmiaDescriptionHandler(helpers.TestHandlerWithPopulatedDB):
    _handler = node.AhmiaDescriptionHandler

    @inlineCallbacks
    def test_get_ahmia_disabled(self):
        handler = self.request({}, role='admin')

        nodedict = helpers.MockDict().dummyNode
        nodedict['ahmia'] = False

        yield admin.update_node(nodedict, True, 'en')

        yield handler.get()
        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 0)

    @inlineCallbacks
    def test_get_ahmia_enabled(self):
        handler = self.request({}, role='admin')

        nodedict = helpers.MockDict().dummyNode
        nodedict['ahmia'] = True
        yield admin.update_node(nodedict, True, 'en')

        yield handler.get()
        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)
        self._handler.validate_message(json.dumps(self.responses[0]), requests.AhmiaDesc)


class TestContextsCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = node.ContextsCollection

    @inlineCallbacks
    def test_get(self):
        handler = self.request({}, role='admin')
        yield handler.get()

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)
        self._handler.validate_message(json.dumps(self.responses[0]), requests.ContextCollectionDesc)


class TestReceiversCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = node.ReceiversCollection

    @inlineCallbacks
    def test_get(self):
        handler = self.request({}, role='admin')
        yield handler.get()

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)
        self._handler.validate_message(json.dumps(self.responses[0]), requests.ReceiverCollectionDesc)
