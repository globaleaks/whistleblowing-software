from twisted.internet.defer import inlineCallbacks, returnValue

from globaleaks import db
from globaleaks.handlers.admin import shorturl
from globaleaks.handlers.base import GLSessions
from globaleaks.models.config import PrivateFactory
from globaleaks.orm import transact
from globaleaks.rest import errors
from globaleaks.security import generateRandomKey
from globaleaks.settings import GLSettings

from globaleaks.tests import helpers


@transact
def set_api_key(store, s):
    PrivateFactory(store).set_val('admin_api_token', s)


class TestAPITokenEnabled(helpers.TestHandlerWithPopulatedDB):
    _handler = shorturl.ShortURLCollection

    @inlineCallbacks
    def setUp(self):
        self.api_key = generateRandomKey(32)
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield set_api_key(self.api_key)
        yield db.refresh_memory_variables()

    @inlineCallbacks
    def test_accept_token(self):
        shorturl_desc = self.get_dummy_shorturl()
        handler = self.request(shorturl_desc, headers={'x-api-token': self.api_key})
        yield handler.post()

    @inlineCallbacks
    def test_deny_token(self):
        shorturl_desc = self.get_dummy_shorturl()
        handler = self.request(shorturl_desc, headers={'x-api-token': 'a'*32})
        yield self.assertRaises(errors.NotAuthenticated, handler.post)

    @inlineCallbacks
    def tearDown(self):
        yield set_api_key('')
        yield helpers.TestHandlerWithPopulatedDB.tearDown(self)


class TestAPITokenDisabled(helpers.TestHandlerWithPopulatedDB):
    _handler = shorturl.ShortURLCollection

    @inlineCallbacks
    def test_deny_token(self):
        # The active component of this application is the placement of the api key
        # in the private memory copy. When that changes this test will break.
        self.api_key = generateRandomKey(32)
        yield set_api_key(self.api_key)
        shorturl_desc = self.get_dummy_shorturl()
        handler = self.request(shorturl_desc, headers={'x-api-token': self.api_key})
        yield self.assertRaises(errors.NotAuthenticated, handler.post)

    @inlineCallbacks
    def tearDown(self):
        yield set_api_key('')
        yield helpers.TestHandlerWithPopulatedDB.tearDown(self)
