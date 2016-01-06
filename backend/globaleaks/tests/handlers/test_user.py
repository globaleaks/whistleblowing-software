# -*- coding: utf-8 -*-
import unittest
import random
from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers
from globaleaks.handlers import admin, user
from globaleaks.rest import errors


class TestUserInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = user.UserInstance

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)

        self.rcvr_id = (yield admin.receiver.get_receiver_list('en'))[0]['id']

    @inlineCallbacks
    def test_get(self):
        handler = self.request(user_id = self.rcvr_id, role='receiver')

        yield handler.get()

    @inlineCallbacks
    def test_put_data_obtained_with_get(self):
        handler = self.request(user_id = self.rcvr_id, role='receiver')

        yield handler.get()

        handler = self.request(self.responses[0], user_id = self.rcvr_id, role='receiver')
        yield handler.put()

    @inlineCallbacks
    def test_put_with_remove_pgp_flag_true(self):
        handler = self.request(user_id = self.rcvr_id, role='receiver')

        yield handler.get()

        self.responses[0]['pgp_key_remove'] = True

        handler = self.request(self.responses[0], user_id = self.rcvr_id, role='receiver')
        yield handler.put()

    @inlineCallbacks
    def test_handler_update_key(self):
        handler = self.request(user_id = self.rcvr_id, role='receiver')

        yield handler.get()

        # check key is initialized at start
        self.assertEqual(self.responses[0]['pgp_key_status'], u'disabled')
        self.assertEqual(self.responses[0]['pgp_key_fingerprint'], u'')
        self.assertEqual(self.responses[0]['pgp_key_public'], u'')
        self.assertEqual(self.responses[0]['pgp_key_info'], u'')
        self.assertEqual(self.responses[0]['pgp_key_expiration'], '1970-01-01T00:00:00Z')

        self.responses[0]['pgp_key_public'] = unicode(helpers.VALID_PGP_KEY1)
        self.responses[0]['pgp_key_status'] = u'disabled' # Test, this field is ignored and set
        self.responses[0]['pgp_key_remove'] = False
        handler = self.request(self.responses[0], user_id=self.rcvr_id, role='receiver')
        yield handler.put() # key update 1

        # check update 1
        self.assertEqual(self.responses[1]['pgp_key_fingerprint'],
            u'CF4A22020873A76D1DCB68D32B25551568E49345')
        self.assertEqual(self.responses[1]['pgp_key_status'], u'enabled')

        self.responses[1]['pgp_key_public'] = unicode(helpers.VALID_PGP_KEY2)
        self.responses[1]['pgp_key_remove'] = False
        handler = self.request(self.responses[1], user_id=self.rcvr_id, role='receiver')
        yield handler.put() # key update 2

        # check update 2
        self.assertEqual(self.responses[2]['pgp_key_fingerprint'], u'7106D296DA80BCF21A3D93056097CE44FED083C9')

        self.responses[2]['pgp_key_remove'] = True
        handler = self.request(self.responses[2], user_id=self.rcvr_id, role='receiver')
        yield handler.put() # removal

        # check removal
        self.assertEqual(self.responses[3]['pgp_key_status'], u'disabled')
        self.assertIsNone(self.responses[3]['pgp_key_fingerprint'])
        self.assertIsNone(self.responses[3]['pgp_key_public'])
        self.assertIsNone(self.responses[3]['pgp_key_info'])
        self.assertEqual(self.responses[3]['pgp_key_expiration'], '1970-01-01T00:00:00Z')

    @inlineCallbacks
    def test_load_malformed_key(self):
        handler = self.request(user_id = self.rcvr_id, role='receiver')

        yield handler.get()

        self.responses[0]['pgp_key_public'] = unicode(helpers.VALID_PGP_KEY1).replace('A', 'B')
        self.responses[0]['pgp_key_status'] = u'disabled' # Test, this field is ignored and set
        self.responses[0]['pgp_key_remove'] = False
        handler = self.request(self.responses[0], user_id=self.rcvr_id, role='receiver')
        yield self.assertFailure(handler.put(), errors.PGPKeyInvalid)
