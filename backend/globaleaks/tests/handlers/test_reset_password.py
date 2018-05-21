# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from six import text_type
from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.orm import transact
from globaleaks.handlers import password_reset
from globaleaks.handlers.admin import receiver
from globaleaks.rest import errors
from globaleaks.tests import helpers
from globaleaks.utils.utility import datetime_now
from globaleaks.state import State

@transact
def set_reset_token(session, user_id, validation_token):
    user = models.db_get(session, models.User, models.User.id == user_id)
    user.change_email_date = datetime_now()
    user.reset_password_token = validation_token
    session.commit()

@transact
def get_user(session, user_id):
    user = models.db_get(session, models.User, models.User.id == user_id)
    session.expunge(user)
    return user

class TestPasswordResetInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = password_reset.PasswordResetHandler

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

        # Get the original password being used
        user_orig = yield get_user(self.rcvr_id)

        yield set_reset_token(
            self.user['id'],
            u"token",
        )

        yield handler.get(u"token")

        # Now we check if the token was update
        user = yield get_user(self.rcvr_id)
        self.assertNotEqual(user.password, user_orig.password)

    @inlineCallbacks
    def test_get_failure(self):
        State.tenant_cache[1]['enable_password_reset'] = True
        handler = self.request()

        # Get the original password being used
        user_orig = yield get_user(self.rcvr_id)

        yield set_reset_token(
            self.user['id'],
            u"token"
        )

        yield handler.get(u"wrong_token")

        # Now we check if the token was update
        user = yield get_user(self.rcvr_id)
        self.assertEqual(user.password, user_orig.password)

    @inlineCallbacks
    def test_get_disabled(self):
        State.tenant_cache[1]['enable_password_reset'] = False
        handler = self.request()

        # Get the original password being used
        user_orig = yield get_user(self.rcvr_id)

        yield set_reset_token(
            self.user['id'],
            u"token"
        )

        yield handler.get(u"token")

        # Now we check if the token was update
        user = yield get_user(self.rcvr_id)
        self.assertNotEqual(user.password, user_orig.password)

    @inlineCallbacks
    def test_post(self):
        State.tenant_cache[1]['enable_password_reset'] = True

        data_request = {
            'username': self.user['username'],
            'mail_address': self.user['mail_address']
        }
        handler = self.request(data_request)

        yield handler.post()

        # Now we check if the token was update
        user = yield get_user(self.rcvr_id)
        self.assertNotEqual(user.reset_password_token, None)
