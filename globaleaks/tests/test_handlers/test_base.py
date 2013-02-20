from twisted.trial import unittest
from globaleaks.rest import errors
from globaleaks.handlers import base
from globaleaks.rest.errors import InvalidInputFormat
from globaleaks.tests import helpers

import json

# class TestBaseHandler(helpers.TestHandler):
#
#     _handler = base.BaseHandler
#
#     validate_jmessage(self, jmessage, message_template)

class MockHandler(base.BaseHandler):

    def __init__(self):
        pass

class TestValidate(unittest.TestCase):

    _handler = base.BaseHandler

    def test_validate_jmessage_valid(self):
        dummy_message = {'spam': 'ham', 'firstd': {3:4}, 'fields': "CIAOCIAO", 'nest':[{1:2, 3:4}]}
        dummy_message_template = {'spam': str, 'firstd': dict, 'fields': '\w+', 'nest': [dict]}

        handler = MockHandler()
        self.assertTrue(handler.validate_jmessage(dummy_message, dummy_message_template))

        dummy_message = {'key': [{'code': 'it', 'name': 'Italiano'}, {'code': 'en', 'name': 'English'}]}
        dummy_message_template = {'key': list}
        self.assertTrue(handler.validate_jmessage(dummy_message, dummy_message_template))

    def test_validate_jmessage_invalid(self):
        dummy_message = {'spam': 'ham', 'fields': "CIAOCIAO" , 'nest':{1: 3, 4: 5}}
        dummy_message_template = {'spam': str, 'fields': '\d+', 'nest' : int}

        handler = MockHandler()

        self.assertRaises(InvalidInputFormat,
            handler.validate_jmessage, dummy_message, dummy_message_template)

    def test_validate_message_valid(self):
        dummy_json = json.dumps({'spam': 'ham'})
        dummy_message_template = {'spam': unicode}

        handler = MockHandler()
        self.assertEqual(json.loads(dummy_json), handler.validate_message(dummy_json, dummy_message_template) )

    def test_validate_message_invalid(self):
        dummy_json = json.dumps({'spam': 'ham'})
        dummy_message_template = {'spam': int}

        handler = MockHandler()

        self.assertRaises(InvalidInputFormat,
            handler.validate_message, dummy_json, dummy_message_template)

    def test_validate_type_valid(self):

        handler = MockHandler()

        self.assertTrue( handler.validate_type('foca', str) )
        self.assertTrue( handler.validate_type(True, bool) )
        self.assertTrue( handler.validate_type(4, int) )
        self.assertTrue( handler.validate_type(u'foca', unicode) )
        self.assertTrue( handler.validate_type(['foca', 'fessa'], list))
        self.assertTrue( handler.validate_type({'foca':1}, dict) )

    def test_validate_type_invalid(self):

        handler = MockHandler()

        self.assertFalse( handler.validate_type(1, str) )
        self.assertFalse( handler.validate_type(1, unicode) )
        self.assertFalse( handler.validate_type(False, unicode) )
        self.assertFalse( handler.validate_type({}, list))
        self.assertFalse( handler.validate_type(True, dict) )

    def test_validate_python_type_valid(self):

        handler = MockHandler()

        self.assertTrue( handler.validate_python_type('foca', str) )
        self.assertTrue( handler.validate_python_type(True, bool) )
        self.assertTrue( handler.validate_python_type(4, int) )
        self.assertTrue( handler.validate_python_type(u'foca', unicode) )
        self.assertTrue( handler.validate_python_type(None, dict) )

    def test_validate_GLtype_valid(self):

        handler = MockHandler()
        self.assertTrue( handler.validate_GLtype('Foca', '\w+') )
        self.assertFalse( handler.validate_GLtype('Foca', '\d+') )


