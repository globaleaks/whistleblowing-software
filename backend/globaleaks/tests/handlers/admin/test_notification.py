# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.db.appdata import load_appdata
from globaleaks.tests import helpers
from globaleaks.handlers import admin

# special guest:

stuff = u"³²¼½¬¼³²"

class TestNotificationInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = admin.notification.NotificationInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        yield handler.get()
        self.assertEqual(self.responses[0]['server'], 'demo.globaleaks.org')

    @inlineCallbacks
    def test_put(self):
        handler = self.request(role='admin')
        yield handler.get()

        self.responses[0]['server'] = stuff

        handler = self.request(self.responses[0], role='admin')
        yield handler.put()
        self.assertEqual(self.responses[1]['server'], stuff)

    @inlineCallbacks
    def test_put_reset_templates(self):
        handler = self.request(role='admin')
        yield handler.get()

        self.responses[0]['reset_templates'] = True

        handler = self.request(self.responses[0], role='admin')
        yield handler.put()

        appdata_dict = load_appdata()
        for k in appdata_dict['templates']:
            self.assertEqual(self.responses[1][k], appdata_dict['templates'][k]['en'])
