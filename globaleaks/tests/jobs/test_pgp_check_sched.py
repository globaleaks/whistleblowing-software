# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

import json

from globaleaks.tests import helpers
from globaleaks.settings import GLSetting, transact, transact_ro
from globaleaks.models import Receiver

from globaleaks.jobs import pgp_check_sched

class TestPGPCheckSchedule(helpers.TestGLWithPopulatedDB):

    @transact
    def remove_receiver_pgpkey_but_set_pgp_enabled(self, store):

        rcvrs = store.find(Receiver)

        for rcvr in rcvrs:
            rcvr.gpg_key_armor = None
            rcvr.gpg_key_status = u'Enabled'

    @transact
    def load_receiver_pgpkey_but_set_pgp_disabled(self, store):

        rcvrs = store.find(Receiver)

        for rcvr in rcvrs:
            rcvr.gpg_key_armor = helpers.VALID_PGP_KEY
            rcvr.gpg_key_status = u'Disabled'

    @transact_ro
    def verify_scheduler_has_disabled_pgp(self, store):
        rcvrs = store.find(Receiver)

        for rcvr in rcvrs:
            self.assertEqual(rcvr.gpg_key_info, None)
            self.assertEqual(rcvr.gpg_key_fingerprint, None)
            self.assertEqual(rcvr.gpg_key_status, u'Disabled')
            self.assertEqual(rcvr.gpg_key_armor, None)
            self.assertEqual(rcvr.gpg_enable_notification, False)

    @transact_ro
    def verify_scheduler_has_enabled_pgp(self, store):
        rcvrs = store.find(Receiver)

        for rcvr in rcvrs:
            self.assertNotEqual(rcvr.gpg_key_info, None)
            self.assertNotEqual(rcvr.gpg_key_fingerprint, None)
            self.assertEqual(rcvr.gpg_key_status, u'Enabled')
            self.assertEqual(rcvr.gpg_key_armor, helpers.VALID_PGP_KEY)
            self.assertEqual(rcvr.gpg_enable_notification, True)

    @inlineCallbacks
    def test_sched_action_on_no_receiver_pgpkey_but_pgp_set_as_enabled(self):

        yield self.remove_receiver_pgpkey_but_set_pgp_enabled()

        yield pgp_check_sched.PGPCheckSchedule().operation()

        yield self.verify_scheduler_has_disabled_pgp()

    @inlineCallbacks
    def test_sched_action_on_receiver_pgpkey_present_but_pgp_set_as_disabled(self):

        yield self.load_receiver_pgpkey_but_set_pgp_disabled()

        yield pgp_check_sched.PGPCheckSchedule().operation()

        yield self.verify_scheduler_has_enabled_pgp()

