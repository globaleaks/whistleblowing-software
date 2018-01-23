# -*- coding: utf-8 -*-
import json

from globaleaks.db.appdata import load_appdata
from globaleaks.handlers import admin
from globaleaks.models import config
from globaleaks.rest import requests
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks

# special guest:

stuff = u"³²¼½¬¼³²"


class TestNotificationInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = admin.notification.NotificationInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        response = yield handler.get()
        self.assertEqual(response['smtp_server'], 'demo.globaleaks.org')

    @inlineCallbacks
    def test_put(self):
        handler = self.request(role='admin')
        notif_desc = yield handler.get()

        notif_desc['smtp_server'] = stuff
        notif_desc['smtp_password'] = u'widdlyscuds'

        handler = self.request(notif_desc, role='admin')
        response = yield handler.put()
        self.assertEqual(response['smtp_server'], stuff)

    @inlineCallbacks
    def test_put_reset_templates(self):
        handler = self.request(role='admin')
        notif_desc = yield handler.get()

        notif_desc['reset_templates'] = True
        notif_desc['smtp_password'] = u'widdlyscuds'

        handler = self.request(notif_desc, role='admin')
        response = yield handler.put()

        appdata_dict = load_appdata()
        for k in appdata_dict['templates']:
            if k in requests.AdminNotificationDesc:
                self.assertEqual(response[k], appdata_dict['templates'][k]['en'])


class TestNotificationTestInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = admin.notification.NotificationTestInstance

    @inlineCallbacks
    def test_post(self):
        handler = self.request(role='admin')
        yield handler.post()
