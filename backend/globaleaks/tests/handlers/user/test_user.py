# -*- coding: utf-8 -*
import base64
import time

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.twofactor.totp import TOTP
from cryptography.hazmat.primitives.hashes import SHA1

from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers import user
from globaleaks.handlers.user.operation import UserOperationHandler
from globaleaks.rest import errors
from globaleaks.tests import helpers
from globaleaks.utils.utility import datetime_null


class TestUserInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = user.UserInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request(user_id=self.dummyReceiver_1['id'], role='receiver')

        yield handler.get()

    @inlineCallbacks
    def test_handler_update_key(self):
        handler = self.request(user_id=self.dummyReceiver_1['id'], role='receiver')

        response = yield handler.get()

        # perform and test key update
        response['pgp_key_public'] = helpers.PGPKEYS['VALID_PGP_KEY2_PUB']
        response['pgp_key_remove'] = False
        handler = self.request(response, user_id=self.dummyReceiver_1['id'], role='receiver')
        response = yield handler.put()

        self.assertEqual(response['pgp_key_fingerprint'],
                         'CECDC5D2B721900E65639268846C82DB1F9B45E2')

        self.assertEqual(response['pgp_key_public'],
                         helpers.PGPKEYS['VALID_PGP_KEY2_PUB'])

        # perform and test key removal
        response['pgp_key_remove'] = True
        handler = self.request(response, user_id=self.dummyReceiver_1['id'], role='receiver')
        response = yield handler.put()

        self.assertEqual(response['pgp_key_fingerprint'], '')
        self.assertEqual(response['pgp_key_public'], '')
        self.assertEqual(response['pgp_key_expiration'], datetime_null())

    @inlineCallbacks
    def test_load_malformed_key(self):
        handler = self.request(user_id=self.dummyReceiver_1['id'], role='receiver')

        response = yield handler.get()

        response['pgp_key_public'] = helpers.PGPKEYS['VALID_PGP_KEY1_PUB'].replace('A', 'B')
        response['pgp_key_remove'] = False
        handler = self.request(response, user_id=self.dummyReceiver_1['id'], role='receiver')
        yield self.assertFailure(handler.put(), errors.InputValidationError)

    @inlineCallbacks
    def test_change_name(self):
        handler = self.request(user_id=self.dummyReceiver_1['id'], role='receiver')

        response = yield handler.get()
        response['name'] = "Test Name"
        handler = self.request(response, user_id=self.dummyReceiver_1['id'], role='receiver')

        response = yield handler.put()
        self.assertEqual(response['name'], 'Test Name')

    @inlineCallbacks
    def test_start_email_change_process(self):
        handler = self.request(user_id=self.dummyReceiver_1['id'], role='receiver')

        response = yield handler.get()

        email = "change1@test.com"
        response['mail_address'] = email
        handler = self.request(response, user_id=self.dummyReceiver_1['id'], role='receiver')
        response = yield handler.put()

        self.assertNotEqual(response['mail_address'], email)
        self.assertEqual(response['change_email_address'], email)

        email = "change2@test.com"
        response['mail_address'] = email
        handler = self.request(response, user_id=self.dummyReceiver_1['id'], role='receiver')
        response = yield handler.put()

        self.assertEqual(response['change_email_address'], email)


class TestUserGetRecoveryKey(helpers.TestHandlerWithPopulatedDB):
    _handler = user.operation.UserOperationHandler

    def test_put(self):
        data_request = {
            'operation': 'get_recovery_key',
            'args': {}
        }

        handler = self.request(data_request, role='receiver')

        return handler.put()


class TestUser2FAEnrollment(helpers.TestHandlerWithPopulatedDB):
    _handler = user.operation.UserOperationHandler

    @inlineCallbacks
    def test_2fa(self):
        totp_secret = 'B6IZ6BEH6BMWDBZ2ND7PGAQN2GIBVOVX'

        # Attempt enrolling for 2FA with an invalid token
        data_request = {
            'operation': 'enable_2fa',
            'args': {
                'secret': totp_secret,
                'token': 'invalid_token'
            }
        }

        handler = self.request(data_request, role='receiver')

        self.assertFailure(handler.put(), errors.InvalidTwoFactorAuthCode)

        # Attempt enrolling for 2FA with a valid token
        totp = TOTP(base64.b32decode(totp_secret), 6, SHA1(), 30, default_backend())
        current_token = totp.generate(time.time()).decode()

        data_request = {
            'operation': 'enable_2fa',
            'args': {
                'secret': totp_secret,
                'token': current_token
            }
        }

        handler = self.request(data_request, role='receiver')

        yield handler.put()

        self.state.TwoFactorTokens.clear()

        data_request = {
            'operation': 'disable_2fa',
            'args': {}
        }


        current_token = totp.generate(time.time()).decode()

        handler = self.request(data_request, role='receiver', headers={'x-confirmation': current_token})

        yield handler.put()


class TestUserOperations(helpers.TestHandlerWithPopulatedDB):
    _handler = UserOperationHandler

    def _test_operation_handler(self, operation, args={}):
        data_request = {
            'operation': operation,
            'args': args
        }

        return self.request(data_request, role='receiver').put()

    @inlineCallbacks
    def test_user_test_change_password(self):
        valid_password = 'validPassword1!'

        weak_passwords = [
            'invalidpassword1!', # no uppercase characters
            'INVALIDPASSWORD1!', # no lowercase characters
            'invalidPassword!!', # no number characters
            'invalidPassword11', # no symbol characters
            'shortP1!'           # short password below 10 characters
        ]

        for password in weak_passwords:
            yield self.assertFailure(self._test_operation_handler('change_password',
                                                                  {'password': password,
                                                                   'current': helpers.VALID_PASSWORD1}),
                                     errors.InputValidationError)

        yield self.assertFailure(self._test_operation_handler('change_password',
                                                              {'password': valid_password,
                                                               'current': 'INVALID_OLD_PASSWORD'}),
                                     errors.InvalidOldPassword)

        yield self._test_operation_handler('change_password',
                                           {'password': valid_password,
                                            'current': helpers.VALID_PASSWORD1})
