# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks
from globaleaks.handlers import shorturl
from globaleaks.handlers.admin import shorturl as admin_shorturl
from globaleaks.rest import errors
from globaleaks.tests import helpers


class TestShortURLCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = shorturl.ShortURL

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        self.assertFailure(handler.get(u'/u/unexistent'), errors.ResourceNotFound)

        for i in range(3):
            req = self.get_dummy_shorturl(str(i))
            yield admin_shorturl.create_shorturl(1, req)
            handler = self.request(role='admin')
            response = yield handler.get(unicode(req['shorturl']))
            self.assertEqual(handler.request.responseHeaders.getRawHeaders('location')[0], req['longurl'])
