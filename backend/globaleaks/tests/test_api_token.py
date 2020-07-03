# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks import db
from globaleaks.handlers.admin import redirect
from globaleaks.models.config import db_set_config_variable
from globaleaks.orm import tw
from globaleaks.rest import errors
from globaleaks.tests import helpers
from globaleaks.utils.crypto import generateApiToken


class TestAPITokenEnabled(helpers.TestHandlerWithPopulatedDB):
    _handler = redirect.RedirectCollection

    @inlineCallbacks
    def setUp(self):
        self.api_tok, digest = generateApiToken()
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield tw(db_set_config_variable, 1, 'admin_api_token_digest', digest)
        yield db.refresh_memory_variables()

    @inlineCallbacks
    def test_accept_token(self):
        desc = self.get_dummy_redirect()
        handler = self.request(desc, headers={'x-api-token': self.api_tok})
        yield handler.post()

    @inlineCallbacks
    def test_deny_token(self):
        desc = self.get_dummy_redirect()
        handler = self.request(desc, headers={'x-api-token': 'a'*32})
        yield self.assertRaises(errors.NotAuthenticated, handler.post)

    @inlineCallbacks
    def tearDown(self):
        yield tw(db_set_config_variable, 1, 'admin_api_token_digest', '')
        yield helpers.TestHandlerWithPopulatedDB.tearDown(self)


class TestAPITokenDisabled(helpers.TestHandlerWithPopulatedDB):
    _handler = redirect.RedirectCollection

    @inlineCallbacks
    def test_deny_token(self):
        # The active component of this application is the placement of the api key
        # in the private memory copy. When that changes this test will break.
        self.api_tok, digest = generateApiToken()
        yield tw(db_set_config_variable, 1, 'admin_api_token_digest', '')

        desc = self.get_dummy_redirect()
        handler = self.request(desc, headers={'x-api-token': self.api_tok})
        yield self.assertRaises(errors.NotAuthenticated, handler.post)

    @inlineCallbacks
    def tearDown(self):
        yield tw(db_set_config_variable, 1, 'admin_api_token_digest', '')
        yield helpers.TestHandlerWithPopulatedDB.tearDown(self)
