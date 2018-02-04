# -*- coding: utf-8 -*-
import json

from globaleaks.handlers.base import BaseHandler
from globaleaks.rest.errors import InputValidationError
from globaleaks.tests import helpers

FUTURE = 100


class BaseHandlerMock(BaseHandler):
    check_roles = 'unauthenticated'

    def get(self):
        return

class TestBaseHandler(helpers.TestHandlerWithPopulatedDB):
    _handler = BaseHandlerMock

    def test_validate_jmessage_valid(self):
        dummy_message = {'spam': 'ham', 'firstd': {3: 4}, 'fields': "CIAOCIAO", 'nest': [{1: 2, 3: 4}]}
        dummy_message_template = {'spam': str, 'firstd': dict, 'fields': '\w+', 'nest': [dict]}

        self.assertTrue(BaseHandler.validate_jmessage(dummy_message, dummy_message_template))

    def test_validate_jmessage_invalid(self):
        dummy_message = {}
        dummy_message_template = {'spam': str, 'firstd': dict, 'fields': '\w+', 'nest': [dict]}

        self.assertRaises(InputValidationError,
                          BaseHandler.validate_jmessage, dummy_message, dummy_message_template)

    def test_validate_message_valid(self):
        dummy_json = json.dumps({'spam': 'ham'})
        dummy_message_template = {'spam': unicode}

        self.assertEqual(json.loads(dummy_json), BaseHandler.validate_message(dummy_json, dummy_message_template))

    def test_validate_message_invalid(self):
        dummy_json = json.dumps({'spam': 'ham'})
        dummy_message_template = {'spam': dict}

        self.assertRaises(InputValidationError,
                          BaseHandler.validate_message, dummy_json, dummy_message_template)

    def test_validate_type_valid(self):
        self.assertTrue(BaseHandler.validate_type('foca', str))
        self.assertTrue(BaseHandler.validate_type(True, bool))
        self.assertTrue(BaseHandler.validate_type(4, int))
        self.assertTrue(BaseHandler.validate_type(u'foca', unicode))
        self.assertTrue(BaseHandler.validate_type(['foca', 'fessa'], list))
        self.assertTrue(BaseHandler.validate_type({'foca': 1}, dict))

    def test_validate_type_invalid(self):
        self.assertFalse(BaseHandler.validate_type(1, str))
        self.assertFalse(BaseHandler.validate_type(1, unicode))
        self.assertFalse(BaseHandler.validate_type(False, unicode))
        self.assertFalse(BaseHandler.validate_type({}, list))
        self.assertFalse(BaseHandler.validate_type(True, dict))

    def test_validate_python_type_valid(self):
        self.assertTrue(BaseHandler.validate_python_type('foca', str))
        self.assertTrue(BaseHandler.validate_python_type(True, bool))
        self.assertTrue(BaseHandler.validate_python_type(4, int))
        self.assertTrue(BaseHandler.validate_python_type(u'foca', unicode))
        self.assertTrue(BaseHandler.validate_python_type(None, dict))

    def test_validate_regexp_valid(self):
        self.assertTrue(BaseHandler.validate_regexp('Foca', '\w+'))
        self.assertFalse(BaseHandler.validate_regexp('Foca', '\d+'))
