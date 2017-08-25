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
        self.assertEqual(response['server'], 'demo.globaleaks.org')

        resp_desc = self.ss_serial_desc(config.NotificationFactory.admin_notification,
                                        requests.AdminNotificationDesc)

        self._handler.validate_message(json.dumps(response), resp_desc)


    @inlineCallbacks
    def test_put(self):
        handler = self.request(role='admin')
        notif_desc = yield handler.get()

        notif_desc['server'] = stuff
        notif_desc['password'] = u'widdlyscuds'

        handler = self.request(notif_desc, role='admin')
        response = yield handler.put()
        self.assertEqual(response['server'], stuff)

    @inlineCallbacks
    def test_put_reset_templates(self):
        handler = self.request(role='admin')
        notif_desc = yield handler.get()

        notif_desc['reset_templates'] = True
        notif_desc['password'] = u'widdlyscuds'

        handler = self.request(notif_desc, role='admin')
        response = yield handler.put()

        appdata_dict = load_appdata()
        for k in appdata_dict['templates']:
            if k in requests.AdminNotificationDesc:
                self.assertEqual(response[k], appdata_dict['templates'][k]['en'])

    @inlineCallbacks
    def test_parse_pgp_options(self):
        handler = self.request(role='admin')
        admin_notif = yield handler.get()

        pk = helpers.PGPKEYS['VALID_PGP_KEY1_PUB']
        admin_notif['exception_email_pgp_key_public'] = pk

        handler = self.request(admin_notif, role='admin')
        response = yield handler.put()

        test_key1_fp = "BFB3C82D1B5F6A94BDAC55C6E70460ABF9A4C8C1"
        self.assertEqual(response['exception_email_pgp_key_public'], pk)
        self.assertEqual(response['exception_email_pgp_key_fingerprint'], test_key1_fp)


class TestNotificationTestInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = admin.notification.NotificationTestInstance

    @inlineCallbacks
    def test_post(self):
        handler = self.request(role='admin')
        yield handler.post()

        # TODO: test email generation
