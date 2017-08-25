# -*- coding: utf-8 -*-
from globaleaks.handlers.admin import context
from globaleaks.models import Context
from globaleaks.rest import errors
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks

# special guest:

stuff = u"³²¼½¬¼³²"


class TestContextsCollection(helpers.TestHandler):
    _handler = context.ContextsCollection

    def test_get(self):
        handler = self.request(role='admin')
        return handler.get()

    @inlineCallbacks
    def test_post(self):
        for attrname in Context.localized_keys:
            self.dummyContext[attrname] = stuff

        handler = self.request(self.dummyContext, role='admin')
        response = yield handler.post()

        self.dummyContext['id'] = response['id']
        self.assertEqual(response['description'], stuff)


class TestContextInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = context.ContextInstance

    @inlineCallbacks
    def test_put(self):
        for attrname in Context.localized_keys:
            self.dummyContext[attrname] = stuff

        handler = self.request(self.dummyContext, role='admin')
        response = yield handler.put(self.dummyContext['id'])
        self.assertEqual(response['description'], stuff)

    @inlineCallbacks
    def test_update_context_timetolive(self):
        self.dummyContext['tip_timetolive'] = 100

        for attrname in Context.localized_keys:
            self.dummyContext[attrname] = stuff

        handler = self.request(self.dummyContext, role='admin')
        response = yield handler.put(self.dummyContext['id'])

        self.assertEqual(response['tip_timetolive'], self.dummyContext['tip_timetolive'])

    @inlineCallbacks
    def test_delete(self):
        handler = self.request(self.dummyContext, role='admin')
        yield handler.delete(self.dummyContext['id'])
        yield self.assertFailure(handler.delete(self.dummyContext['id']),
                                 errors.ContextIdNotFound)
