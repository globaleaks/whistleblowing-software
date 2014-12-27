# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers import admin
from globaleaks.handlers.node import anon_serialize_field
from globaleaks.handlers.admin import create_context
from globaleaks.handlers.admin.field import create_field
from globaleaks import models
from globaleaks.rest import requests, errors
from globaleaks.settings import transact, transact_ro
from globaleaks.tests import helpers

@transact
def get_step_id(store, context_id):
    steps = store.find(models.Step, models.Step.context_id == context_id)
    return steps[0].id

def get_sample_field():
    sample_field = {
        'is_template': True,
        'step_id': '',
        'fieldgroup_id': '',
        'label': u'antani',
        'type': u'inputbox',
        'preview': False,
        'description': u"field description",
        'hint': u'field hint',
        'multi_entry': False,
        'stats_enabled': False,
        'required': False,
        'options': [],
        'children': [],
        'y': 1,
        'x': 1,
    }
    return sample_field

class TestFieldCreate(helpers.TestHandler):
        _handler = admin.field.FieldCreate
        fixtures = ['fields.json']

        @inlineCallbacks
        def test_post(self):
            """
            Attempt to create a new field via a post request.
            """
            attrs = get_sample_field()
            attrs['is_template'] = False
            self.dummyContext = yield create_context(self.dummyContext, 'en')
            attrs['step_id'] = yield get_step_id(self.dummyContext['id'])
            handler = self.request(attrs, role='admin')
            yield handler.post()
            self.assertEqual(len(self.responses), 1)

            resp, = self.responses
            self.assertIn('id', resp)
            self.assertNotEqual(resp.get('options'), None)


class TestFieldUpdate(helpers.TestHandler):
        _handler = admin.field.FieldUpdate
        fixtures = ['fields.json']

        @transact_ro
        def _get_children(self, store, field_id):
            field = models.Field.get(store, field_id)
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
            Create a new field, the get it back using the receieved id.
            """
            attrs = get_sample_field()
            attrs['is_template'] = False
            self.dummyContext = yield create_context(self.dummyContext, 'en')
            attrs['step_id'] = yield get_step_id(self.dummyContext['id'])
            field = yield create_field(attrs, 'en')

            handler = self.request(role='admin')
            yield handler.get(field['id'])
            self.assertEqual(len(self.responses), 1)
            self.assertEqual(field['id'], self.responses[0]['id'])

        @inlineCallbacks
        def test_put(self):
            """
            Attempt to update a field, changing its type via a put request.
            """
            attrs = get_sample_field()
            attrs['is_template'] = False
            self.dummyContext = yield create_context(self.dummyContext, 'en')
            attrs['step_id'] = yield get_step_id(self.dummyContext['id'])
            field = yield create_field(attrs, 'en')

            updated_sample_field = get_sample_field()
            updated_sample_field['is_template'] = False
            self.dummyContext = yield create_context(self.dummyContext, 'en')
            updated_sample_field['step_id'] = yield get_step_id(self.dummyContext['id'])
            updated_sample_field.update(type='inputbox')
            handler = self.request(updated_sample_field, role='admin')
            yield handler.put(field['id'])
            self.assertEqual(len(self.responses), 1)
            self.assertEqual(field['id'], self.responses[0]['id'])
            self.assertEqual(self.responses[0]['type'], 'inputbox')

            wrong_sample_field = get_sample_field()
            attrs['is_template'] = False
            attrs['step_id'] = yield get_step_id(self.dummyContext['id'])
            wrong_sample_field.update(type='nonexistingfieldtype')
            handler = self.request(wrong_sample_field, role='admin')
            self.assertFailure(handler.put(field['id']), errors.InvalidInputFormat)

        @inlineCallbacks
        def test_delete(self):
            """
            Create a new field, then attempt to delete it.
            """
            attrs = get_sample_field()
            attrs['is_template'] = False
            self.dummyContext = yield create_context(self.dummyContext, 'en')
            attrs['step_id'] = yield get_step_id(self.dummyContext['id'])
            field = yield create_field(attrs, 'en')

            handler = self.request(role='admin')
            yield handler.delete(field['id'])
            self.assertEqual(handler.get_status(), 200)
            # second deletion operation should fail
            self.assertFailure(handler.delete(field['id']), errors.FieldIdNotFound)


class TestFieldsCollection(helpers.TestHandlerWithPopulatedDB):
        _handler = admin.field.FieldsCollection
        fixtures = ['fields.json']

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
            self.assertIn('17121164-0d0f-4180-9e9c-b1f72e815105', ids)
            self.assertGreater(types.count('fieldgroup'), 0)

            # check tha childrens are not present in the list
            # as the list should contain only parents fields
            for field in fields:
                for child in field['children']:
                    self.assertNotIn(child, ids)

class TestFieldTemplateCreate(helpers.TestHandlerWithPopulatedDB):
        _handler = admin.field.FieldTemplateCreate
        fixtures = ['fields.json']

        @inlineCallbacks
        def test_post(self):
            """
            Attempt to create a new field via a post request.
            """
            handler = self.request(get_sample_field(), role='admin')
            yield handler.post()
            self.assertEqual(len(self.responses), 1)

            resp, = self.responses
            self.assertIn('id', resp)
            self.assertNotEqual(resp.get('options'), None)


class TestFieldTemplateUpdate(helpers.TestHandlerWithPopulatedDB):
        _handler = admin.field.FieldTemplateUpdate
        fixtures = ['fields.json']

        @transact_ro
        def _get_field(self, store, field_id):
            field = models.Field.get(store, field_id)
            return anon_serialize_field(store, field, 'en')

        @transact_ro
        def _get_children(self, store, field_id):
            field = models.Field.get(store, field_id)
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
            Create a new field, the get it back using the receieved id.
            """
            field = yield create_field(get_sample_field(), 'en')

            handler = self.request(role='admin')
            yield handler.get(field['id'])
            self.assertEqual(len(self.responses), 1)
            self.assertEqual(field['id'], self.responses[0]['id'])

        @inlineCallbacks
        def test_put_1(self):
            """
            Attempt to update a field, changing its type via a put request.
            """
            field = yield create_field(get_sample_field(), 'en')

            updated_sample_field = get_sample_field()
            updated_sample_field.update(type='inputbox')
            handler = self.request(updated_sample_field, role='admin')
            yield handler.put(field['id'])
            self.assertEqual(len(self.responses), 1)
            self.assertEqual(field['id'], self.responses[0]['id'])
            self.assertEqual(self.responses[0]['type'], 'inputbox')

            wrong_sample_field = get_sample_field()
            wrong_sample_field.update(type='nonexistingfieldtype')
            handler = self.request(wrong_sample_field, role='admin')
            self.assertFailure(handler.put(field['id']), errors.InvalidInputFormat)

        @inlineCallbacks
        def test_put_2(self):
            """
            Update the field tree with nasty stuff, like cyclic graphs, inexisting ids.
            """
            generalities_fieldgroup_id = '37242164-1b1f-1110-1e1c-b1f12e815105'
            sex_field_id = '98891164-1a0b-5b80-8b8b-93b73b815156'
            surname_field_id = '25521164-1d0f-5f80-8e8c-93f73e815156'
            name_field_id = '25521164-0d0f-4f80-9e9c-93f72e815105'
            invalid_id = '00000000-1d0f-5f80-8e8c-93f700000000'

            handler = self.request(role='admin')
            yield handler.get(generalities_fieldgroup_id)

            # simple edits shall work
            sex_field = yield self._get_field(sex_field_id)
            surname_field = yield self._get_field(surname_field_id)

            self.responses[0]['children'] = [sex_field,
                                             surname_field]

            handler = self.request(self.responses[0], role='admin')
            yield handler.put(generalities_fieldgroup_id)
            yield self.assert_model_exists(models.Field, generalities_fieldgroup_id)

            # parent MUST not refer to itself in child
            generalities_fieldgroup = yield self._get_field(generalities_fieldgroup_id)
            self.responses[0]['children'] = [generalities_fieldgroup]
            handler = self.request(self.responses[0], role='admin')
            self.assertFailure(handler.put(generalities_fieldgroup_id), errors.InvalidInputFormat)

            # a child not of type 'fieldgroup' MUST never have children.
            yield handler.get(name_field_id)
            sex_field = yield self._get_field(sex_field_id)
            self.responses[2]['children'] = [sex_field]
            handler = self.request(self.responses[2], role='admin')
            self.assertFailure(handler.put(name_field_id), errors.InvalidInputFormat)
            yield self.assert_is_not_child(name_field_id, sex_field_id)


        @inlineCallbacks
        def test_delete(self):
            """
            Create a new field, then attempt to delete it.
            """
            attrs = get_sample_field()
            field = yield create_field(attrs, 'en')

            handler = self.request(role='admin')
            yield handler.delete(field['id'])
            self.assertEqual(handler.get_status(), 200)
            # second deletion operation should fail
            self.assertFailure(handler.delete(field['id']), errors.FieldIdNotFound)


class TestFieldTemplatesCollection(helpers.TestHandlerWithPopulatedDB):
        _handler = admin.field.FieldTemplatesCollection
        fixtures = ['fields.json']

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
            self.assertIn('27121164-0d0f-4180-9e9c-b1f72e815105', ids)
            self.assertGreater(types.count('fieldgroup'), 0)

            # check tha childrens are not present in the list
            # as the list should contain only parents fields
            for field in fields:
                for child in field['children']:
                    self.assertNotIn(child, ids)
