# -*- coding: utf-8 -*-
import random
import json

from twisted.internet.defer import inlineCallbacks

from globaleaks import __version__
from globaleaks.rest.errors import InvalidInputFormat
from globaleaks.tests import helpers
from globaleaks.rest import requests, errors
from globaleaks.handlers.admin import context
from globaleaks.models import Context

# special guest:

stuff = u"³²¼½¬¼³²"


class TestContextsCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = context.ContextsCollection

    def test_get(self):
        handler = self.request(role='admin')
        return handler.get()


class TestContextsCreate(helpers.TestHandlerWithPopulatedDB):
    _handler = context.ContextCreate

    @inlineCallbacks
    def test_post(self):
        for attrname in Context.localized_strings:
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
        for attrname in Context.localized_strings:
            self.dummyContext[attrname] = stuff

        handler = self.request(self.dummyContext, role='admin')
        yield handler.put(self.dummyContext['id'])
        self.assertEqual(self.responses[0]['description'], stuff)

    @inlineCallbacks
    def test_update_context_timetolive(self):
        self.dummyContext['tip_timetolive'] = 100  # days

        for attrname in Context.localized_strings:
            self.dummyContext[attrname] = stuff

        handler = self.request(self.dummyContext, role='admin')
        yield handler.put(self.dummyContext['id'])

        self.assertEqual(self.responses[0]['tip_timetolive'], self.dummyContext['tip_timetolive'])

    @inlineCallbacks
    def test_update_context_invalid_timetolive(self):
        self.dummyContext['tip_timetolive'] = -3  # days

        for attrname in Context.localized_strings:
            self.dummyContext[attrname] = stuff

        # 1000 hours are more than three days, and a Tip can't live less than a submission
        handler = self.request(self.dummyContext, role='admin')

        yield self.assertFailure(handler.put(self.dummyContext['id']), errors.InvalidTipTimeToLive)

    @inlineCallbacks
    def test_delete(self):
        handler = self.request(self.dummyContext, role='admin')
        yield handler.delete(self.dummyContext['id'])
        yield self.assertFailure(handler.get(self.dummyContext['id']),
                                 errors.ContextIdNotFound)
