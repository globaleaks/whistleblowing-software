# -*- coding: utf-8 -*-
from globaleaks import models
from globaleaks.handlers import support
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestSupportionHandler(helpers.TestHandler):
    _handler = support.SupportHandler

    @inlineCallbacks
    def test_post(self):
        request = {
            'mail_address': 'giovanni.pellerano@globaleaks.org',
            'text': 'The email is to ask support for...'
        }

        yield self.test_model_count(models.Mail, 0)
        handler = self.request(request)
        yield handler.post()
        self.assertEqual(handler.request.code, 200)
        yield self.test_model_count(models.Mail, 2)
