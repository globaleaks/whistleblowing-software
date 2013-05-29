import os
from twisted.internet.defer import inlineCallbacks
from twisted.trial import unittest

from globaleaks.tests import helpers
from globaleaks.rest import errors
from globaleaks.security import import_gpg_key, gpg_encrypt
from globaleaks.handlers import receiver
from globaleaks.settings import GLSetting
from globaleaks.utils import timelapse_represent
from globaleaks.models import Receiver

from globaleaks.plugins.notification import MailNotification
from globaleaks.plugins.base import Event

GPGROOT = "/tmp/"

class TestPrettyUtils(unittest.TestCase):

    def test_pretty_years(self):

        # values expressed in seconds
        one_hour = 3600
        one_day = one_hour * 24
        one_year = one_day * 365

        self.assertEqual(timelapse_represent(one_hour), "1 hour")
        self.assertEqual(timelapse_represent(one_day), "1 day")
        self.assertEqual(timelapse_represent(one_year), "1 year")


class TestReceiverSetKey(helpers.TestHandler):
    _handler = receiver.ReceiverInstance

    def _clean_gpg_env(self):
        """
        utility function called just to clean/fix path
        """
        GLSetting.gpgroot = GPGROOT
        pubring_file = os.path.join(GLSetting.gpgroot, "pubring.gpg")

        if os.path.isfile(pubring_file):
            os.unlink(pubring_file)
        else:
            os.mkdir(GLSetting.gpgroot)

    @inlineCallbacks
    def test_get(self):

        handler = self.request(self.dummyReceiver, role='receiver', user_id=self.dummyReceiver['receiver_gus'])
        yield handler.get()
        self.assertEqual(self.responses[0]['gpg_key_info'], None)

    @inlineCallbacks
    def test_update_key(self):

        self._clean_gpg_env()

        receiver_only_update = {
            'gpg_key_armor': unicode(DummyKeyClass.__doc__),
            'gpg_key_disable': False,
            'name' : "irrelevant",
            'password' : "",
            'old_password': "",
            'username' : "irrelevant",
            'notification_fields' : {'mail_address': 'am_i_ignored_or_not@email.xxx'},
            'description' : "A new description"
        }
        handler = self.request(receiver_only_update, role='receiver', user_id=self.dummyReceiver['receiver_gus'])
        yield handler.put()

        self.assertEqual(self.responses[0]['gpg_key_fingerprint'],
            u'341F1A8CE2B4F4F4174D7C21B842093DC6765430')

        # do not consider in this check the result of put, but inquiry the GET output
        self.request(role='receiver', user_id=self.dummyReceiver['receiver_gus'])
        yield handler.get()

        self.assertTrue(self.responses[0].has_key('gpg_key_info'))
        self.assertTrue(self.responses[0]['gpg_key_info'].find('341F1A8CE2B4F4F4174D7C21B842093DC6765430') > 0 )
        self.assertTrue(self.responses[0]['gpg_key_status'], Receiver._gpg_types[1] )


    def test_handler_put_malformed_gpg_key(self):

        self._clean_gpg_env()

        receiver_only_update = {
            # here key corruption happen:
            'gpg_key_armor': unicode(DummyKeyClass.__doc__).replace('A', 'B'),
            'gpg_key_disable': False,
            'name' : "irrelevant",
            'password' : "",
            'old_password': "",
            'username' : "irrelevant",
            'notification_fields' : {'mail_address': 'am_i_ignored_or_not@email.xxx'},
            'description' : "A new description"
        }

        handler = self.request(receiver_only_update, role='receiver', user_id=self.dummyReceiver['receiver_gus'])
        d = handler.put()
        self.assertFailure(d, errors.GPGKeyInvalid)
        return d

    def test_gpg_encryption(self):

        mail_support = MailNotification()

        node_notif_templ = "%EventTime% %NodeName% %ContextName%"

        receiver_desc = {
                'username': 'vecna@useless_information_on_this_test.org',
                'name': 'assertion',
                'gpg_key_fingerprint': '341F1A8CE2B4F4F4174D7C21B842093DC6765430' }

        mock_event = Event(type=u'tip', trigger='Tip',
                    notification_settings= node_notif_templ,
                    trigger_info={'creation_date': '2013-05-13T17:49:26.105485', 'id': 'useless' },
                    node_info={'name': 'dummy name',
                               'hidden_service': 'useless',
                               'public_site': 'useless' },
                    receiver_info=receiver_desc,
                    context_info={'name': 'all our bases belong to you' },
                    plugin=MailNotification()  )

        mail_content = mail_support.format_template(node_notif_templ, mock_event)

        # setup the GPG key before
        GLSetting.gpgroot = GPGROOT
        gpg_key_armor = unicode(DummyKeyClass.__doc__)
        gpg_info, gpg_fingerprint = import_gpg_key(receiver_desc['username'], gpg_key_armor)

        self.assertEqual(gpg_fingerprint, receiver_desc['gpg_key_fingerprint'])
        encrypted_body = gpg_encrypt(mail_content, receiver_desc)

        # The test shall be done decrypting this data, but this would need a
        # keypair that I can't pregenerate in the test.
        self.assertGreater(len(encrypted_body), 20)



class DummyKeyClass:
    """
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1.4.11 (GNU/Linux)

mQGiBEqTwO0RBACqVdgJXs/vKv76HIudqQc9y/xSLoCxGd8mAxqjXn9fONAIrzDY
j79s1UMFCS8iTEH9EQGyv0JfCKXUcD1HFmKfZO8YfiBSM17SS+inPuV5+ZeQxvNh
ppzgit4jx+0DVMgBWYf/CvT5mPAFzA1U7mZFid/y/ITvEDeq42beOOXYkwCg/bUT
iw4R+Z0Q6LX++xhcidAQvqcD/iDACormazMFabPg45Bf7/lIHor2wGkzx46FuXbu
nxYyUXJQ88mU7szbhHdYhD2a3J1R/fUXuLsgQophWFBCKkq4YC3GKksKlQGKPgdS
WMxjxel4iaQJ5IZ48M+W/Y0eT+DSvARZw+IUr3q89JhS7mcxISlbocLz9Z32AGIj
olcxBACNUw6cJ7p5nCYjw9f+KQyU0NNx2/hGg+SBLRWiV5SaIarGDJG/KHurvsOA
yzjLEupXQvtaEyh5IeRu3rGr4hAfbtsIXRw8E055VBkwzXRN1rpcvumzayMW+OT8
M5lbU8u/5+PNTfmjOJsLdp40WWBRQrCr1F/xu3lyjQg0P78gu7QwQ2xhdWRpbyBB
Z29zdGkgPGNsYXVkaW8uYWdvc3RpQGxvZ2lvc2hlcm1lcy5vcmc+iGgEExEIACgC
GwMFCQfDDL8GCwkIBwMCBhUIAgkKCwQWAgMBAh4BAheABQJQeqODAAoJELhCCT3G
dlQwFfoAoIHqBJwQXb4uggiGJyqhLBENcU1XAKDIKet7mFlE4r3gfaWCmjevm+TT
MrQ7dmVjbmEgKGEgUmFuZG9tIEdsb2JhTGVrcyBEZXZlbG9wZXIpIDx2ZWNuYUBn
bG9iYWxlYWtzLm9yZz6IaAQTEQgAKAUCUHWpWAIbAwUJB8MMvwYLCQgHAwIGFQgC
CQoLBBYCAwECHgECF4AACgkQuEIJPcZ2VDDJVQCfbrtSyDNA3PSco8ILcPOUDSXr
sYAAn0X93PosYlznhqA3iiqEjPJm7X10tBh2ZWNuYSA8dmVjbmFAczBmdHBqLm9y
Zz6IawQTEQgAKwIbAwUJB8MMvwYLCQgHAwIGFQgCCQoLBBYCAwECHgECF4AFAlB6
o4MCGQEACgkQuEIJPcZ2VDBwlQCgu6Izv6NgQDKceRl43WWImtnJy0UAoPJNU3PW
r8q9nN64lzqRLxA27YPmtBx2ZWNuYSA8dmVjbmFAZGVsaXJhbmRvbS5uZXQ+iGgE
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
=bDVx
-----END PGP PUBLIC KEY BLOCK-----

    """
    pass
