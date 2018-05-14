# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from six import text_type
from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.orm import transact
from globaleaks.handlers import email_validation
from globaleaks.handlers.admin import receiver
from globaleaks.rest import errors
from globaleaks.tests import helpers
from globaleaks.utils.utility import datetime_now

@transact
def set_email_token(session, user_id, validation_token, email):
    user = models.db_get(session, models.User, models.User.id == user_id)
    user.change_email_date = datetime_now()
    user.change_email_token = validation_token
    user.change_email_address = email


class TestEmailValidationInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = email_validation.EmailValidation

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)

        for r in (yield receiver.get_receiver_list(1, 'en')):
            if r['pgp_key_fingerprint'] == u'BFB3C82D1B5F6A94BDAC55C6E70460ABF9A4C8C1':
                self.rcvr_id = r['id']
                self.user = r

    @inlineCallbacks
    def test_get_success(self):
        handler = self.request()
        yield set_email_token(
            self.user['id'],
            u"token",
            u"test@changeemail.com"
        )

        yield handler.get(u"token")

        # Now we check if the token was update
        for r in (yield receiver.get_receiver_list(1, 'en')):
            if r['pgp_key_fingerprint'] == u'BFB3C82D1B5F6A94BDAC55C6E70460ABF9A4C8C1':
                self.assertEqual(r['mail_address'], 'test@changeemail.com')

    @inlineCallbacks
    def test_get_failure(self):
        handler = self.request()
        yield set_email_token(
            self.user['id'],
            u"token",
            u"test@changeemail.com"
        )

        yield handler.get(u"wrong_token")

        # Now we check if the token was update
        for r in (yield receiver.get_receiver_list(1, 'en')):
            if r['pgp_key_fingerprint'] == u'BFB3C82D1B5F6A94BDAC55C6E70460ABF9A4C8C1':
                self.assertNotEqual(r['mail_address'], 'test@changeemail.com')
