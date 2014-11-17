# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers import admin
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
        'template_id': '',
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

class TestFieldUpdate(helpers.TestHandlerWithPopulatedDB):
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
            attrs['step_id'] = yield get_step_id(self.dummyContext['id'])
            field = yield create_field(attrs, 'en')

            updated_sample_field = get_sample_field()
            updated_sample_field['is_template'] = False
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
            attrs['step_id'] = yield get_step_id(self.dummyContext['id'])
            field = yield create_field(attrs, 'en')

            handler = self.request(role='admin')
            yield handler.delete(field['id'])
            self.assertEqual(handler.get_status(), 200)
            # second deletion operation should fail
            self.assertFailure(handler.delete(field['id']), errors.FieldIdNotFound)

        def test_create_field_associated_to_step(self):
            pass


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
            self.assertIn('15521164-1d0f-5f80-8e8c-93f73e815156', ids)
            self.assertGreater(types.count('fieldgroup'), 0)

            # check children are present in the list as well
            for field in fields:
                for child in field['children']:
                    self.assertIn(child, ids)

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
            self.responses[0]['children'] = [sex_field_id, surname_field_id]

            handler = self.request(self.responses[0], role='admin')
            yield handler.put(generalities_fieldgroup_id)
            yield self.assert_model_exists(models.Field, generalities_fieldgroup_id)

            # parent MUST not refer to itself in child
            self.responses[0]['children'] = [generalities_fieldgroup_id]
            handler = self.request(self.responses[0], role='admin')
            self.assertFailure(handler.put(generalities_fieldgroup_id), errors.InvalidInputFormat)

            # a child not of type 'fieldgroup' MUST never have children.
            yield handler.get(name_field_id)
            self.responses[2]['children'] = [sex_field_id]
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

        def test_create_field_associated_to_step(self):
            pass


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
            self.assertIn('25521164-1d0f-5f80-8e8c-93f73e815156', ids)
            self.assertGreater(types.count('fieldgroup'), 0)

            # check children are present in the list as well
            for field in fields:
                for child in field['children']:
                    self.assertIn(child, ids)


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
