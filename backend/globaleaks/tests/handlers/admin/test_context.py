# -*- coding: utf-8 -*-
import json

from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.admin import context
from globaleaks.models import Context
from globaleaks.rest import requests, errors
from globaleaks.tests import helpers

# special guest:

stuff = u"³²¼½¬¼³²"


class TestContextsCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = context.ContextsCollection

    def test_get(self):
        handler = self.request(role='admin')
        return handler.get()

    @inlineCallbacks
    def test_post(self):
        for attrname in Context.localized_keys:
            self.dummyContext[attrname] = stuff

        handler = self.request(self.dummyContext, role='admin')
        yield handler.post()

        self.dummyContext['id'] = self.responses[0]['id']
        self.assertEqual(self.responses[0]['description'], stuff)


class TestContextInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = context.ContextInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        yield handler.get(self.dummyContext['id'])
        self._handler.validate_message(json.dumps(self.responses[0]), requests.AdminContextDesc)

    @inlineCallbacks
    def test_put(self):
        for attrname in Context.localized_keys:
            self.dummyContext[attrname] = stuff

        handler = self.request(self.dummyContext, role='admin')
        yield handler.put(self.dummyContext['id'])
        self.assertEqual(self.responses[0]['description'], stuff)

    @inlineCallbacks
    def test_update_context_timetolive(self):
        self.dummyContext['tip_timetolive'] = 100

        for attrname in Context.localized_keys:
            self.dummyContext[attrname] = stuff

        handler = self.request(self.dummyContext, role='admin')
        yield handler.put(self.dummyContext['id'])

        self.assertEqual(self.responses[0]['tip_timetolive'], self.dummyContext['tip_timetolive'])

    @inlineCallbacks
    def test_delete(self):
        handler = self.request(self.dummyContext, role='admin')
        yield handler.delete(self.dummyContext['id'])
        yield self.assertFailure(handler.get(self.dummyContext['id']),
                                 errors.ContextIdNotFound)
