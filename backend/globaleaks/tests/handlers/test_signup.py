# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks
from globaleaks.handlers import signup
from globaleaks.models import config
from globaleaks.orm import transact
from globaleaks.rest import errors
from globaleaks.tests import helpers


@transact
def enable_signup(session):
    config.ConfigFactory(session, 1, 'node').set_val(u'enable_signup', True)


class TestSignup(helpers.TestHandler):
    _handler = signup.Signup

    def test_post_with_signup_disabled(self):
        handler = self.request(self.dummySignup)
        return self.assertFailure(handler.post(), errors.ForbiddenOperation)

    @inlineCallbacks
    def test_post_with_signup_enabled(self):
        yield enable_signup()

        handler = self.request(self.dummySignup)
        yield handler.post()


class TestSignupActivation(helpers.TestHandler):
    _handler = signup.SignupActivation

    def test_get_with_signup_disabled(self):
        handler = self.request(self.dummySignup)
        return self.assertFailure(handler.get(u'valid_or_invalid'), errors.ForbiddenOperation)

    @inlineCallbacks
    def test_get_with_valid_activation_token(self):
        yield enable_signup()

        self._handler = signup.Signup
        handler = self.request(self.dummySignup)
        r = yield handler.post()

        self._handler = signup.SignupActivation
        handler = self.request(self.dummySignup)
        r = yield handler.get(r['signup']['activation_token'])

        self.assertTrue('admin_login_url' in r)

    @inlineCallbacks
    def test_get_with_invalid_activation_token(self):
        yield enable_signup()

        handler = self.request(self.dummySignup)
        r = yield handler.get(u'invalid')

        self.assertTrue(not r)

