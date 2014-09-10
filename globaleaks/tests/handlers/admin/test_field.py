# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import os
import random

from twisted.internet.defer import inlineCallbacks

from globaleaks import __version__
from globaleaks.handlers import admin, admstaticfiles
from globaleaks.models import Node, Context, Receiver
from globaleaks.rest.errors import InvalidInputFormat
from globaleaks.rest import requests, errors
from globaleaks.settings import GLSetting
from globaleaks.utils.utility import uuid4
from globaleaks.tests import helpers


class TestAdminFieldInstance(helpers.TestHandler):
        _handler = admin.field.FieldInstance
        sample_request = {
            'label': '{"en": "test label"}',
            'description': '{"en": "test description"}',
            'hint': '{"en": "test hint"}',
            'multi_entry': False,
            'type': 'checkbox',
            'options': {},
            'required': False,
            'preview': False,
            'stats_enabled': True,
            'x': 0,
            'y': 0
        }

        @inlineCallbacks
        def test_get(self):
            """
            Create a new field, the get it back using the receieved id.
            """
            handler = self.request(self.sample_request, role='admin')
            yield handler.post()
            self.assertEqual(len(self.responses), 1)
            self.assertIn('id', self.responses[0])

            field_id = self.responses[0]['id']
            yield handler.get(field_id)
            self.assertEqual(len(self.responses), 2)
            self.assertEqual(field_id, self.responses[1]['id'])

        @inlineCallbacks
        def test_post(self):
            """
            Attempt to create a new field via a post request.
            """
            handler = self.request(self.sample_request, role='admin')
            yield handler.post()
            self.assertEqual(len(self.responses), 1)

            resp, = self.responses
            self.assertIn('id', resp)
            self.assertNotEqual(resp.get('options'), None)

        @inlineCallbacks
        def test_put(self):
            """
            Attempt to update a field, changing its type via a put request.
            """
            handler = self.request(self.sample_request, role='admin')
            yield handler.post()
            self.assertEqual(len(self.responses), 1)
            field_id = self.responses[0].get('id')
            self.assertIsNotNone(field_id)

            updated_sample_request = self.sample_request
            updated_sample_request.update(type='inputbox')
            handler = self.request(updated_sample_request, role='admin')
            yield handler.put(field_id)
            self.assertEqual(len(self.responses), 2)
            self.assertNotEqual(self.responses[0], self.responses[1])
            self.assertEqual(field_id, self.responses[1]['id'])
            self.assertEqual(self.responses[1]['type'], 'inputbox')

            wrong_sample_request = self.sample_request
            wrong_sample_request.update(type='nonexistingfieldtype')
            handler = self.request(wrong_sample_request, role='admin')
            self.assertFailure(handler.put(field_id), errors.InvalidInputFormat)


        @inlineCallbacks
        def test_delete(self):
            """
            Create a new field, then attempt to delete it.
            """
            handler = self.request(self.sample_request, role='admin')
            yield handler.post()
            self.assertEqual(len(self.responses), 1)
            field_id = self.responses[0].get('id')
            self.assertIsNotNone(field_id)

            handler = self.request(self.responses[0], role='admin')
            yield handler.delete(field_id)
            self.assertEqual(handler.get_status(), 200)
            # second deletion operation should fail
            self.assertFailure(handler.delete(field_id), errors.FieldIdNotFound)


class TestAdminFieldsCollection(helpers.TestHandler):
        _handler = admin.field.FieldsCollection
        fixtures = ['fields.json']

        @inlineCallbacks
        def test_get(self):
            handler = self.request(role='admin')
            yield handler.get()
