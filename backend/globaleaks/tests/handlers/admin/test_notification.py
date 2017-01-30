# -*- coding: utf-8 -*-
import json

from twisted.internet.defer import inlineCallbacks

from globaleaks.db.appdata import load_appdata
from globaleaks.handlers import admin
from globaleaks.models import config
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

        notif_desc = self.responses[0]
        notif_desc['server'] = stuff
        notif_desc['password'] = u'widdlyscuds'

        handler = self.request(notif_desc, role='admin')
        yield handler.put()
        self.assertEqual(self.responses[1]['server'], stuff)

    @inlineCallbacks
    def test_put_reset_templates(self):
        handler = self.request(role='admin')
        yield handler.get()

        notif_desc = self.responses[0]
        notif_desc['reset_templates'] = True
        notif_desc['password'] = u'widdlyscuds'

        handler = self.request(notif_desc, role='admin')
        yield handler.put()

        appdata_dict = load_appdata()
        for k in appdata_dict['templates']:
            self.assertEqual(self.responses[1][k], appdata_dict['templates'][k]['en'])

    @inlineCallbacks
    def test_parse_pgp_options(self):
        handler = self.request(role='admin')
        yield handler.get()
        admin_notif = self.responses[0]
        pk = helpers.PGPKEYS['VALID_PGP_KEY1_PUB']
        admin_notif['exception_email_pgp_key_public'] = pk


        handler = self.request(admin_notif, role='admin')
        yield handler.put()

        resp = self.responses[1]
        test_key1_fp = "ECAF2235E78E71CD95365843C7B190543CAA7585"
        self.assertEqual(resp['exception_email_pgp_key_public'], pk)
        self.assertEqual(resp['exception_email_pgp_key_fingerprint'], test_key1_fp)


class TestNotificationTestInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = admin.notification.NotificationTestInstance

    @inlineCallbacks
    def test_post(self):
        handler = self.request(role='admin')
        yield handler.post()

        # TODO: test email generation
