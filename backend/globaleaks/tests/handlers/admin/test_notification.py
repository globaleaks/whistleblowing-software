# -*- coding: utf-8 -*-
import json

from twisted.internet.defer import inlineCallbacks

from globaleaks.db.appdata import load_appdata
from globaleaks.models import config
from globaleaks.handlers import admin
from globaleaks.rest import requests
from globaleaks.tests import helpers

# special guest:

stuff = u"³²¼½¬¼³²"


class TestNotificationInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = admin.notification.NotificationInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        yield handler.get()
        self.assertEqual(self.responses[0]['server'], 'demo.globaleaks.org')

        resp_desc = self.ss_serial_desc(config.NotificationFactory.admin_notification,
                                        requests.AdminNotificationDesc)

        self._handler.validate_message(json.dumps(self.responses[0]), resp_desc)

    @inlineCallbacks
    def test_put(self):
        handler = self.request(role='admin')
        yield handler.get()

        self.responses[0]['server'] = stuff
        self.responses[0]['password'] = u'widdlyscuds'

        handler = self.request(self.responses[0], role='admin')
        yield handler.put()
        self.assertEqual(self.responses[1]['server'], stuff)

    @inlineCallbacks
    def test_put_reset_templates(self):
        handler = self.request(role='admin')
        yield handler.get()

        self.responses[0]['reset_templates'] = True
        self.responses[0]['password'] = u'widdlyscuds'

        handler = self.request(self.responses[0], role='admin')
        yield handler.put()

        appdata_dict = load_appdata()
        for k in appdata_dict['templates']:
            self.assertEqual(self.responses[1][k], appdata_dict['templates'][k]['en'])


class TestNotificationTestInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = admin.notification.NotificationTestInstance

    @inlineCallbacks
    def test_post(self):
        handler = self.request(role='admin')
        yield handler.post()

        # TODO: test email generation
