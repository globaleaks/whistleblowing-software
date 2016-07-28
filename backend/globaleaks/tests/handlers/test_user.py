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

        # check that the key is initialized at start
        self.assertNotEqual(self.responses[0]['pgp_key_public'], u'')

        self.assertEqual(self.responses[0]['pgp_key_fingerprint'],
                         u'ECAF2235E78E71CD95365843C7B190543CAA7585')

        self.assertEqual(self.responses[0]['pgp_key_public'],
                         helpers.PGPKEYS['VALID_PGP_KEY1_PUB'])

        self.assertEqual(self.responses[0]['pgp_key_expiration'], '1970-01-01T00:00:00Z')

        # perform and test key update
        self.responses[0]['pgp_key_public'] = unicode(helpers.PGPKEYS['VALID_PGP_KEY2_PUB'])
        self.responses[0]['pgp_key_remove'] = False
        handler = self.request(self.responses[0], user_id=self.rcvr_id, role='receiver')
        yield handler.put()

        self.assertEqual(self.responses[1]['pgp_key_fingerprint'],
                         u'CECDC5D2B721900E65639268846C82DB1F9B45E2')

        self.assertEqual(self.responses[1]['pgp_key_public'],
                         helpers.PGPKEYS['VALID_PGP_KEY2_PUB'])

        # perform and test key removal
        self.responses[1]['pgp_key_remove'] = True
        handler = self.request(self.responses[1], user_id=self.rcvr_id, role='receiver')
        yield handler.put()

        self.assertIsNone(self.responses[2]['pgp_key_fingerprint'])
        self.assertIsNone(self.responses[2]['pgp_key_public'])
        self.assertEqual(self.responses[2]['pgp_key_expiration'], '1970-01-01T00:00:00Z')

    @inlineCallbacks
    def test_load_malformed_key(self):
        handler = self.request(user_id = self.rcvr_id, role='receiver')

        yield handler.get()

        self.responses[0]['pgp_key_public'] = unicode(helpers.PGPKEYS['VALID_PGP_KEY1_PUB']).replace('A', 'B')
        self.responses[0]['pgp_key_remove'] = False
        handler = self.request(self.responses[0], user_id=self.rcvr_id, role='receiver')
        yield self.assertFailure(handler.put(), errors.PGPKeyInvalid)
