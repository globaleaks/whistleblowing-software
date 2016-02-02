# -*- coding: utf-8 -*-
import copy

from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers import admin
from globaleaks.handlers.admin.context import create_context
from globaleaks.handlers.admin.step import create_step
from globaleaks.rest import errors
from globaleaks.tests import helpers


class TestStepCollection(helpers.TestHandler):
        _handler = admin.step.StepCollection

        @inlineCallbacks
        def test_post(self):
            """
            Attempt to create a new step via a post request.
            """
            context = yield create_context(copy.deepcopy(self.dummyContext), 'en')
            step = self.get_dummy_step()
            step['context_id'] = context['id']
            handler = self.request(step, role='admin')
            yield handler.post()
            self.assertEqual(len(self.responses), 1)

            resp, = self.responses
            self.assertIn('id', resp)
            self.assertNotEqual(resp.get('context_id'), None)


class TestStepInstance(helpers.TestHandler):
        _handler = admin.step.StepInstance

        @inlineCallbacks
        def test_get(self):
            """
            Create a new step, then get it back using the received id.
            """
            context = yield create_context(copy.deepcopy(self.dummyContext), 'en')
            step = self.get_dummy_step()
            step['context_id'] = context['id']
            step = yield create_step(step, 'en')

            handler = self.request(role='admin')
            yield handler.get(step['id'])
            self.assertEqual(len(self.responses), 1)
            self.assertEqual(step['id'], self.responses[0]['id'])

        @inlineCallbacks
        def test_put(self):
            """
            Attempt to update a step, changing it presentation order
            """
            context = yield create_context(copy.deepcopy(self.dummyContext), 'en')
            step = self.get_dummy_step()
            step['context_id'] = context['id']
            step = yield create_step(step, 'en')

            step['presentation_order'] = 666

            handler = self.request(step, role='admin')
            yield handler.put(step['id'])
            self.assertEqual(len(self.responses), 1)
            self.assertEqual(step['id'], self.responses[0]['id'])
            self.assertEqual(self.responses[0]['presentation_order'], 666)

        @inlineCallbacks
        def test_delete(self):
            """
            Create a new step, then attempt to delete it.
            """
            context = yield create_context(copy.deepcopy(self.dummyContext), 'en')
            step = self.get_dummy_step()
            step['context_id'] = context['id']
            step = yield create_step(step, 'en')

            handler = self.request(role='admin')
            yield handler.delete(step['id'])
            self.assertEqual(handler.get_status(), 200)
            # second deletion operation should fail
            self.assertFailure(handler.delete(step['id']), errors.StepIdNotFound)
