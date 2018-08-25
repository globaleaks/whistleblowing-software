# -*- coding: utf-8 -*-
from datetime import timedelta

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.orm import transact
from globaleaks.handlers import password_reset
from globaleaks.handlers.admin import receiver
from globaleaks.tests import helpers
from globaleaks.utils.utility import datetime_now
from globaleaks.state import State

@transact
def set_reset_token(session, user_id, validation_token):
    user = models.db_get(session, models.User, models.User.id == user_id)
    user.change_email_date = datetime_now()
    user.reset_password_token = validation_token


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
        State.tenant_cache[1]['enable_password_reset'] = True

        handler = self.request()

        # Get the original password being used
        user_orig = yield get_user(self.rcvr_id)

        yield set_reset_token(
            self.user['id'],
            u"token",
        )

        yield handler.get(u"token")

        # Check if the token was resetted
        user = yield get_user(self.rcvr_id)
        self.assertEqual(user.reset_password_token, None)


    @inlineCallbacks
    def test_get_failure(self):
        State.tenant_cache[1]['enable_password_reset'] = True

        handler = self.request()

        user_orig = yield get_user(self.rcvr_id)

        yield set_reset_token(
            self.user['id'],
            u"token"
        )

        yield handler.get(u"wrong_token")

        # Check if the token was resetted
        user = yield get_user(self.rcvr_id)
        self.assertNotEqual(user.reset_password_token, None)


    @inlineCallbacks
    def test_post(self):
        State.tenant_cache[1]['enable_password_reset'] = True

        data_request = {
            'username_or_email': self.user['username']
        }
        handler = self.request(data_request)

        yield handler.post()

        # Check if the token has been issued
        user = yield get_user(self.rcvr_id)
        self.assertNotEqual(user.reset_password_token, None)

        # Check that an mail has been created
        yield self.test_model_count(models.Mail, 1)
