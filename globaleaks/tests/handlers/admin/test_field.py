# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers import admin
from globaleaks.models import Field
from globaleaks.rest import requests, errors
from globaleaks.settings import transact_ro
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


class TestAdminFieldCollection(helpers.TestHandler):
        _handler = admin.field.FieldsCollection
        fixtures = ['fields.json']

        @transact_ro
        def _get_children(self, store, field_id):
            field = Field.get(store, field_id)
            return [child.id for child in field.children]

        @inlineCallbacks
        def assert_is_child(self, child_id, field_id):
            children = yield self._get_children(field_id)
            self.assertIn(child_id, children)

        @inlineCallbacks
        def assert_is_not_child(self, child_id, field_id):
            children = yield self._get_children(field_id)
            self.assertNotIn(child_id, children)

        @inlineCallbacks
        def test_get(self):
            """
            Retrieve a list of all fields, and verify that they do exist in the
            database.
            """
            handler = self.request(role='admin')
            yield handler.get()
            fields, = self.responses

            ids = [field.get('id') for field in fields]
            types = [field.get('type') for field in fields]
            self.assertGreater(len(fields), 0)
            self.assertNotIn(None, ids)
            self.assertIn('25521164-1d0f-5f80-8e8c-93f73e815156', ids)
            self.assertGreater(types.count('fieldgroup'), 0)

            # check children are present in the list as well
            for field in fields:
                for child in field['children']:
                    self.assertIn(child, ids)

        @inlineCallbacks
        def test_put(self):
            """
            Update the field tree with nasty stuff, like cyclic graphs, inexisting ids.
            """
            generalities_fieldgroup_id = '37242164-1b1f-1110-1e1c-b1f12e815105'
            sex_field_id = '98891164-1a0b-5b80-8b8b-93b73b815156'
            surname_field_id = '25521164-1d0f-5f80-8e8c-93f73e815156'
            name_field_id = '25521164-0d0f-4f80-9e9c-93f72e815105'
            invalid_id = '00000000-1d0f-5f80-8e8c-93f700000000'
            # simple edits shall work
            good_tree = [{
                'id': generalities_fieldgroup_id,
                'children': [sex_field_id, surname_field_id],
            }]
            handler = self.request(good_tree, role='admin')
            yield handler.put()
            yield self.assert_model_exists(Field, generalities_fieldgroup_id)
            yield self.assert_is_child(sex_field_id, generalities_fieldgroup_id)
            yield self.assert_is_not_child(name_field_id,
                                           generalities_fieldgroup_id)
            # parent id MUST exist
            invalid_tree = [{
                'id': invalid_id,
                'children': [name_field_id, sex_field_id]  * 3,
            }]
            handler = self.request(invalid_tree, role='admin')
            self.assertFailure(handler.put(), errors.InvalidInputFormat)
            # child ids MUST exist
            invalid_tree = [{
                'id': generalities_fieldgroup_id,
                'children': [name_field_id, invalid_id, sex_field_id] * 100,
            }]
            handler = self.request(invalid_tree, role='admin')
            self.assertFailure(handler.put(), errors.InvalidInputFormat)
            yield self.assert_is_not_child(invalid_id, generalities_fieldgroup_id)
            yield self.assert_is_child(sex_field_id, generalities_fieldgroup_id)
            yield self.assert_is_not_child(name_field_id,
                                           generalities_fieldgroup_id)
            # parent MUST not refer to itself in child
            # XXX. shall test with a bigger connected component
            recursing_tree = [{
                'id': generalities_fieldgroup_id,
                'children': [generalities_fieldgroup_id],
            }]
            self.assertFailure(handler.put(), errors.InvalidInputFormat)
            # a child not of type 'fieldgroup' MUST never have children.
            invalid_tree = [{
                'id': name_field_id,
                'children': [sex_field_id],
            }]
            self.assertFailure(handler.put(), errors.InvalidInputFormat)
