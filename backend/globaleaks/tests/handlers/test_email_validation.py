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

@transact
def void_email_token(session, validation_token):
    token = session.query(models.EmailValidations).filter(
        models.EmailValidations.validation_token == validation_token
    ).first()

    token.creation_date = datetime.now()+timedelta(days=100)
    session.flush()

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
        token = yield email_validation.generate_email_change_token(
            self.user['id'],
            "test@test.com"
        )

        yield handler.get(token)

        # Now we check if the token was update
        for r in (yield receiver.get_receiver_list(1, 'en')):
            if r['pgp_key_fingerprint'] == u'BFB3C82D1B5F6A94BDAC55C6E70460ABF9A4C8C1':
                self.assertEqual(r['mail_address'], 'test@test.com')

    @inlineCallbacks
    def test_get_failure(self):
        handler = self.request()
        token = yield email_validation.generate_email_change_token(
            self.user['id'],
            "test2@test2.com"
        )

        yield void_email_token(token)
        yield handler.get(token)

        # Now we check if the token was update
        for r in (yield receiver.get_receiver_list(1, 'en')):
            if r['pgp_key_fingerprint'] == u'BFB3C82D1B5F6A94BDAC55C6E70460ABF9A4C8C1':
                self.assertNotEqual(r['mail_address'], 'test2@test2.com')
