# -*- coding: utf-8 -*-
from globaleaks.handlers import admin, user
from globaleaks.handlers.admin import receiver
from globaleaks.rest import errors
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestUserInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = user.UserInstance

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)

        self.rcvr_id = (yield receiver.get_receiver_list(1, 'en'))[0]['id']

    @inlineCallbacks
    def test_get(self):
        handler = self.request(user_id = self.rcvr_id, role='receiver')

        yield handler.get()

    @inlineCallbacks
    def test_put_change_password(self):
        handler = self.request(user_id = self.rcvr_id, role='receiver')

        response = yield handler.get()
        response['password'] = 'new 1337 password!'
        response['old_password'] = helpers.VALID_PASSWORD1

        handler = self.request(response, user_id = self.rcvr_id, role='receiver')
        yield handler.put()

    @inlineCallbacks
    def test_put_with_remove_pgp_flag_true(self):
        handler = self.request(user_id = self.rcvr_id, role='receiver')

        response = yield handler.get()

        response['pgp_key_remove'] = True

        handler = self.request(response, user_id = self.rcvr_id, role='receiver')
        yield handler.put()

    @inlineCallbacks
    def test_handler_update_key(self):
        handler = self.request(user_id = self.rcvr_id, role='receiver')

        response = yield handler.get()

        # check that the key is initialized at start

        self.assertNotEqual(response['pgp_key_public'], u'')

        self.assertEqual(response['pgp_key_fingerprint'],
                         u'BFB3C82D1B5F6A94BDAC55C6E70460ABF9A4C8C1')

        self.assertEqual(response['pgp_key_public'],
                         helpers.PGPKEYS['VALID_PGP_KEY1_PUB'])

        self.assertEqual(response['pgp_key_expiration'], '1970-01-01T00:00:00Z')

        # perform and test key update
        response['pgp_key_public'] = unicode(helpers.PGPKEYS['VALID_PGP_KEY2_PUB'])
        response['pgp_key_remove'] = False
        handler = self.request(response, user_id=self.rcvr_id, role='receiver')
        response = yield handler.put()

        self.assertEqual(response['pgp_key_fingerprint'],
                         u'CECDC5D2B721900E65639268846C82DB1F9B45E2')

        self.assertEqual(response['pgp_key_public'],
                         helpers.PGPKEYS['VALID_PGP_KEY2_PUB'])

        # perform and test key removal
        response['pgp_key_remove'] = True
        handler = self.request(response, user_id=self.rcvr_id, role='receiver')
        response = yield handler.put()

        self.assertEqual(response['pgp_key_fingerprint'], '')
        self.assertEqual(response['pgp_key_public'], '')
        self.assertEqual(response['pgp_key_expiration'], '1970-01-01T00:00:00Z')

    @inlineCallbacks
    def test_load_malformed_key(self):
        handler = self.request(user_id = self.rcvr_id, role='receiver')

        response = yield handler.get()

        response['pgp_key_public'] = unicode(helpers.PGPKEYS['VALID_PGP_KEY1_PUB']).replace('A', 'B')
        response['pgp_key_remove'] = False
        handler = self.request(response, user_id=self.rcvr_id, role='receiver')
        yield self.assertFailure(handler.put(), errors.PGPKeyInvalid)
