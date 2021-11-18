# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers import password_reset
from globaleaks.handlers.admin.user import db_get_users
from globaleaks.orm import db_get, transact, tw
from globaleaks.tests import helpers
from globaleaks.utils.utility import datetime_now


@transact
def set_reset_token(session, user_id, validation_token):
    user = db_get(session, models.User, models.User.id == user_id)
    user.reset_password_token = validation_token
    user.reset_password_date = datetime_now()


class TestPasswordResetInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = password_reset.PasswordResetHandler

    @inlineCallbacks
    def test_post(self):
        data_request = {
            'username': self.dummyReceiver_1['username']
        }

        handler = self.request(data_request)

        yield handler.post()

        # Check that an mail has been created
        yield self.test_model_count(models.Mail, 1)

    @inlineCallbacks
    def test_put(self):
        yield set_reset_token(
            self.dummyReceiver_1['id'],
            u"valid_reset_token"
        )

        # Wrong token
        handler = self.request({'reset_token': 'wrong_token', 'recovery_key': '', 'auth_code': ''})
        ret = yield handler.put()
        self.assertEqual(ret['status'], 'invalid_reset_token_provided')

        # Missing recovery key
        handler = self.request({'reset_token': 'valid_reset_token', 'recovery_key': '', 'auth_code': ''})
        ret = yield handler.put()
        self.assertEqual(ret['status'], 'require_recovery_key')

        # Wrong recovery key
        handler = self.request({'reset_token': 'valid_reset_token', 'recovery_key': 'wrong_recovery_key', 'auth_code': ''})
        ret = yield handler.put()
        self.assertEqual(ret['status'], 'require_recovery_key')

        # Success
        handler = self.request({'reset_token': 'valid_reset_token', 'recovery_key': helpers.USER_REC_KEY_PLAIN, 'auth_code': ''})
        ret = yield handler.put()
        self.assertEqual(ret['status'], 'success')
