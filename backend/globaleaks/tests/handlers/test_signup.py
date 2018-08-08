# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks
from globaleaks import models
from globaleaks.models.config import set_config_variable
from globaleaks.handlers import signup
from globaleaks.orm import transact
from globaleaks.rest import errors
from globaleaks.tests import helpers


@transact
def enable_signup(session):
    models.config.ConfigFactory(session, 1, 'node').set_val(u'enable_signup', True)


@transact
def get_signup_token(session):
    return session.query(models.Signup.activation_token).first()[0]


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
    def test_get_with_valid_activation_token_mode_default(self):
        yield enable_signup()

        yield self.test_model_count(models.User, 0)

        self._handler = signup.Signup
        handler = self.request(self.dummySignup)
        yield handler.post()

        self._handler = signup.SignupActivation
        handler = self.request(self.dummySignup)
        token = yield get_signup_token()
        yield handler.get(token)

        yield self.test_model_count(models.User, 2)

    @inlineCallbacks
    def test_get_with_valid_activation_token_mode_whistleblowing_it(self):
        yield enable_signup()

        yield set_config_variable(1, u'signup_mode', u'whistleblowing.it')

        yield self.test_model_count(models.User, 0)

        self._handler = signup.Signup
        handler = self.request(self.dummySignup)
        r = yield handler.post()

        self._handler = signup.SignupActivation
        handler = self.request(self.dummySignup)
        token = yield get_signup_token()
        yield handler.get(token)
        yield self.test_model_count(models.User, 1)

    @inlineCallbacks
    def test_get_with_invalid_activation_token(self):
        yield enable_signup()

        handler = self.request(self.dummySignup)
        r = yield handler.get(u'invalid')

        self.assertTrue(not r)
