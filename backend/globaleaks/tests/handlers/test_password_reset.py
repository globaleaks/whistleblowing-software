# -*- coding: utf-8 -*-
from datetime import timedelta

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers import password_reset
from globaleaks.handlers.admin import user
from globaleaks.orm import transact
from globaleaks.state import State
from globaleaks.tests import helpers
from globaleaks.utils.utility import datetime_now


@transact
def set_reset_token(session, user_id, validation_token):
    user = models.db_get(session, models.User, models.User.id == user_id)
    user.change_email_date = datetime_now()
    user.reset_password_token = validation_token
    user.reset_password_date = datetime_now()


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

        State.tenant_cache[1]['enable_password_reset'] = True

        for r in (yield user.get_receiver_list(1, 'en')):
            if r['pgp_key_fingerprint'] == u'BFB3C82D1B5F6A94BDAC55C6E70460ABF9A4C8C1':
                self.rcvr_id = r['id']
                self.user = r

    @inlineCallbacks
    def test_post(self):
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

    @inlineCallbacks
    def test_put(self):
        yield set_reset_token(
            self.user['id'],
            u"correct_reset_token"
        )

        # Wrong token
        handler = self.request({'reset_token': 'wrong_token', 'recovery_key': ''})
        ret = yield handler.put()
        self.assertEqual(ret['status'], 'invalid_reset_token_provided')

        # Missing recovery key
        handler = self.request({'reset_token': 'correct_reset_token', 'recovery_key': ''})
        ret = yield handler.put()
        self.assertEqual(ret['status'], 'require_recovery_key')

        # Wrong recovery key
        handler = self.request({'reset_token': 'correct_reset_token', 'recovery_key': 'wrong_recovery_key'})
        ret = yield handler.put()
        self.assertEqual(ret['status'], 'invalid_recovery_key_provided')

        # Success
        handler = self.request({'reset_token': 'correct_reset_token', 'recovery_key': helpers.USER_REC_KEY_PLAIN})
        ret = yield handler.put()
        self.assertEqual(ret['status'], 'success')
