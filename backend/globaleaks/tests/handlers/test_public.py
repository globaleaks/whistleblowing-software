# -*- coding: utf-8 -*-
import json

from twisted.internet.defer import inlineCallbacks
from globaleaks.rest import requests
from globaleaks.tests import helpers
from globaleaks.handlers import admin, public


class TestAhmiaDescriptionHandler(helpers.TestHandlerWithPopulatedDB):
    _handler = public.AhmiaDescriptionHandler

    @inlineCallbacks
    def test_get_ahmia_disabled(self):
        handler = self.request({}, role='admin')

        nodedict = helpers.MockDict().dummyNode
        nodedict['ahmia'] = False

        yield admin.node.update_node(nodedict, 'en')

        yield handler.get()

    @inlineCallbacks
    def test_get_ahmia_enabled(self):
        handler = self.request({}, role='admin')

        nodedict = helpers.MockDict().dummyNode
        nodedict['ahmia'] = True
        yield admin.node.update_node(nodedict, 'en')

        yield handler.get()

        self._handler.validate_message(json.dumps(self.responses[0]), requests.AhmiaDesc)


class TestRobotstxtHandlerHandler(helpers.TestHandlerWithPopulatedDB):
    _handler = public.RobotstxtHandler

    @inlineCallbacks
    def test_get_with_indexing_disabled(self):
        handler = self.request({}, role='admin')

        nodedict = helpers.MockDict().dummyNode
        nodedict['allow_indexing'] = False

        yield admin.node.update_node(nodedict, 'en')

        yield handler.get()

        self.assertEqual(self.responses[0], "User-agent: *\nDisallow: /")

    @inlineCallbacks
    def test_get_with_indexing_enabled(self):
        handler = self.request({}, role='admin')

        nodedict = helpers.MockDict().dummyNode
        nodedict['allow_indexing'] = True
        yield admin.node.update_node(nodedict, 'en')

        yield handler.get()

        self.assertEqual(self.responses[0], "User-agent: *\nAllow: /")


class TestPublicResource(helpers.TestHandlerWithPopulatedDB):
    _handler = public.PublicResource

    @inlineCallbacks
    def test_get(self):
        handler = self.request({}, role='admin')
        yield handler.get()

        self._handler.validate_message(json.dumps(self.responses[0]), requests.PublicResourcesDesc)
