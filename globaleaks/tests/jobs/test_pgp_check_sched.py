# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

import json

from globaleaks.tests import helpers
from globaleaks.settings import GLSetting, transact, transact_ro
from globaleaks.models import Receiver

from globaleaks.jobs import pgp_check_sched

valid_pgp_armor = """
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1

mI0EU29mpgEEALgXe9KSyy24q+6S5U075tawlYFsMor7vEhBzaGOCYgt01Jw3dkm
qQmWcNHPkaHTUz3l3p7qBQCDxBXqoee3LPxJ6yRNX4hbiihRN/NnQ5puchFpVewt
mHs+VU6lJjMsiqP6Vfsi2+DBtO+2IgQDNVyImZAZBJc0fs4VhukdG0UzABEBAAG0
GkFudGFuaSA8YW50YW5pQGFudGFuaS5vcmc+iLgEEwECACIFAlNvZqYCGwMGCwkI
BwMCBhUIAgkKCwQWAgMBAh4BAheAAAoJEBOFXb+BK+yrmnwD/ROpPQuuT1yrXfn0
AE+Yb5q35tkNjhA9amVRfKudF1XFoWYiyYvM3f7EUpbcN9BRtzAZk7waL+WTks9X
5FGHfLCnRvuwEwYc1KUUNMhXIrCoGrCfT1W24eWrQYXxcD1bzIbLf+7m/vU8mCzN
bPSGKLR65/V0w2UqAJK1S8w+r/OpuI0EU29mpgEEAL85nNX2J578hvNobkQn/V9i
vmMODNQ8Sv/912/sb86yIyjF0N8e4MwfWBxXmR3ucUFuy4nCcRxh4Pa0AKv60ltm
GJVNK3J3U3+uKZb+j7og677CHl0msB7p3qdC4d+tVxP4hKmqDTCDuq/bcGk2e4iS
+CsGvJ57zH3lBfyIyR7nABEBAAGInwQYAQIACQUCU29mpgIbDAAKCRAThV2/gSvs
q/ACA/9w2H56hTtt4FNROKVYqu62xdbkPKOYHt/R9eSpOyc6DusDcQ6BsUFBhbsN
8bDiTVnK6N1PA8/+zqHbfE2JPAuEpKrG/lBY51lbfdAdQQ3OgApqkoTQ0e/Le9Ix
oOh6SYNp/FDAcx0Ay7JsVw1gGd82vBwImoGf7D/cLlljnKUyOw==
=C4Tz
-----END PGP PUBLIC KEY BLOCK-----
"""

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
            rcvr.gpg_key_armor = valid_pgp_armor
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
            self.assertEqual(rcvr.gpg_key_armor, valid_pgp_armor)
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

