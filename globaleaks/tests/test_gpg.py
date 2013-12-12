# -*- encoding: utf-8 -*-

import os
import datetime
from twisted.internet import threads
from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers
from globaleaks.rest import errors
from globaleaks.security import GLBGPG, gpg_options_parse, get_expirations
from globaleaks.handlers import receiver, files
from globaleaks.handlers.admin import admin_serialize_receiver, create_receiver, create_context, get_context_list
from globaleaks.handlers.submission import create_submission, update_submission
from globaleaks.settings import GLSetting, transact_ro
from globaleaks.tests.helpers import MockDict
from globaleaks.models import Receiver
from globaleaks.jobs.delivery_sched import APSDelivery, get_files_by_itip, get_receiverfile_by_itip
from globaleaks.plugins.notification import MailNotification
from globaleaks.plugins.base import Event
from globaleaks.utils.templating import Templating

GPGROOT = os.path.join(os.getcwd(), "testing_dir", "gnupg")


@transact_ro
def transact_dummy_whatever(store, receiver_id, mock_request):
    receiver = store.find(Receiver, Receiver.id == receiver_id).one()
    gpg_options_parse(receiver, mock_request)
    return admin_serialize_receiver(receiver)


class TestReceiverSetKey(helpers.TestHandler):
    _handler = receiver.ReceiverInstance

    receiver_desc = {
        'username': 'evilaliv3@useless_information_on_this_test.org',
        'name': 'assertion',
        'gpg_key_fingerprint': 'C1ED5C8FDB6A1C74A807569591EC9BB8D9A950DE',
        'gpg_key_status': Receiver._gpg_types[1] }

    receiver_only_update = {
        'gpg_key_armor': None, 'gpg_key_remove': False,
        "gpg_key_info": None, "gpg_key_fingerprint": None,
        'gpg_key_status': Receiver._gpg_types[0], # Disabled
        "gpg_enable_notification": False,  "gpg_enable_files": False,
        'name' : "irrelevant",
        'password' : "",
        'old_password': "",
        'username' : "irrelevant",
        'mail_address': 'am_i_ignored_or_not@email.xxx',
        'description' : "A new description",
        "comment_notification": True,
        "file_notification": True,
        "tip_notification": False,
        "message_notification": False,
    }

    @inlineCallbacks
    def test_get(self):

        handler = self.request(self.dummyReceiver, role='receiver', user_id=self.dummyReceiver['receiver_gus'])
        yield handler.get()
        self.assertEqual(self.responses[0]['gpg_key_info'], None)

    @inlineCallbacks
    def test_default_encryption_enable(self):

        self.receiver_only_update = dict(MockDict().dummyReceiver)

        self.receiver_only_update['password'] = self.dummyReceiver['password']
        self.receiver_only_update['old_password'] = self.dummyReceiver['password']
        self.receiver_only_update['gpg_key_armor'] = unicode(DeveloperKey.__doc__)
        self.receiver_only_update['gpg_key_status'] = None # Test, this field is ignored and set
        self.receiver_only_update['gpg_key_remove'] = False
        handler = self.request(self.receiver_only_update, role='receiver', user_id=self.dummyReceiver['receiver_gus'])
        yield handler.put()
        self.assertEqual(self.responses[0]['gpg_key_fingerprint'],
                         u'C1ED5C8FDB6A1C74A807569591EC9BB8D9A950DE')
        self.assertEqual(self.responses[0]['gpg_key_status'], Receiver._gpg_types[1])

        self.receiver_only_update['gpg_key_armor'] = unicode(HermesGlobaleaksKey.__doc__)
        self.assertEqual(self.responses[0]['gpg_enable_notification'], True)
        self.assertEqual(self.responses[0]['gpg_enable_files'], True)

    @inlineCallbacks
    def test_handler_update_key(self):

        self.receiver_only_update = dict(MockDict().dummyReceiver)

        self.receiver_only_update['password'] = self.dummyReceiver['password']
        self.receiver_only_update['old_password'] = self.dummyReceiver['password']
        self.receiver_only_update['gpg_key_armor'] = unicode(DeveloperKey.__doc__)
        self.receiver_only_update['gpg_key_status'] = None # Test, this field is ignored and set
        self.receiver_only_update['gpg_key_remove'] = False
        handler = self.request(self.receiver_only_update, role='receiver', user_id=self.dummyReceiver['receiver_gus'])
        yield handler.put()
        self.assertEqual(self.responses[0]['gpg_key_fingerprint'],
            u'C1ED5C8FDB6A1C74A807569591EC9BB8D9A950DE')
        self.assertEqual(self.responses[0]['gpg_key_status'], Receiver._gpg_types[1])

        self.receiver_only_update['gpg_key_armor'] = unicode(HermesGlobaleaksKey.__doc__)
        self.receiver_only_update['gpg_key_remove'] = False
        handler = self.request(self.receiver_only_update, role='receiver', user_id=self.dummyReceiver['receiver_gus'])
        yield handler.put()
        self.assertEqual(self.responses[1]['gpg_key_fingerprint'],
            u'12CB52E0D793A11CAF0360F8839B5DED0050B3C1')
        # and the key has been updated!

    @inlineCallbacks
    def test_transact_malformed_key(self):
        self.receiver_only_update = dict(MockDict().dummyReceiver)
        self.receiver_only_update['gpg_key_armor'] = unicode(DeveloperKey.__doc__).replace('A', 'B')
        self.receiver_only_update['gpg_key_status'] = None # Test, this field is ignored and set
        self.receiver_only_update['gpg_key_remove'] = False

        try:
            serialized_result = yield transact_dummy_whatever(self.dummyReceiver['receiver_gus'],
                self.receiver_only_update)
            print "Invalid results!"
            self.assertTrue(False)
        except errors.GPGKeyInvalid:

            self.assertTrue(True)
        except Exception as excep:
            print "Invalid exception! %s" % excep
            self.assertTrue(False)

    def test_Class_encryption_message(self):

        dummy_template = { "en" : "In %EventTime% you've got a crush for Taryn Southern, yay!!"
                            "more info on: https://www.youtube.com/watch?v=C7JZ4F3zJdY "
                            "and know that you're not alone!" }

        mock_event = Event(type=u'encrypted_tip', trigger='Tip',
                    notification_settings = dummy_template,
                    trigger_info = {'creation_date': '2013-05-13T17:49:26.105485', 'id': 'useless' },
                    node_info = MockDict().dummyNode,
                    receiver_info = MockDict().dummyReceiver,
                    context_info = MockDict().dummyContext,
                    plugin = MailNotification() )

        mail_content = Templating().format_template(dummy_template['en'], mock_event)

        # setup the GPG key before
        GLSetting.gpgroot = GPGROOT

        fake_receiver_desc = {
            'gpg_key_armor': unicode(DeveloperKey.__doc__),
            'gpg_key_fingerprint': u"C1ED5C8FDB6A1C74A807569591EC9BB8D9A950DE",
            'gpg_key_status': Receiver._gpg_types[1],
            'username': u'fake@username.net',
        }

        gpob = GLBGPG(fake_receiver_desc)
        self.assertTrue(gpob.validate_key(DeveloperKey.__doc__))

        encrypted_body = gpob.encrypt_message(mail_content)
        self.assertSubstring('-----BEGIN PGP MESSAGE-----', encrypted_body)

    def test_Class_encryption_file(self):

        # setup the GPG key before
        GLSetting.gpgroot = GPGROOT

        tempsource = os.path.join(os.getcwd(), "temp_source.txt")
        with file(tempsource, 'w+') as f:
            f.write("\n\nDecrypt the Cat!\n\nhttp://tobtu.com/decryptocat.php\n\n")

            f.seek(0)

            fake_receiver_desc = {
                'gpg_key_armor': unicode(DeveloperKey.__doc__),
                'gpg_key_status': Receiver._gpg_types[1],
                'gpg_key_fingerprint': u"C1ED5C8FDB6A1C74A807569591EC9BB8D9A950DE",
                'username': u'fake@username.net',
                }

            # these are the same lines used in delivery_sched.py
            gpoj = GLBGPG(fake_receiver_desc)
            gpoj.validate_key(DeveloperKey.__doc__)
            encrypted_file_path, encrypted_file_size = gpoj.encrypt_file(tempsource, f, "/tmp")
            gpoj.destroy_environment()

            with file(encrypted_file_path, "r") as f:
                first_line = f.readline()

            self.assertSubstring('-----BEGIN PGP MESSAGE-----', first_line)

            with file(encrypted_file_path, "r") as f:
                whole = f.read()
            self.assertEqual(encrypted_file_size, len(whole))

    @inlineCallbacks
    def test_expired_key_error(self):

        self.receiver_only_update['gpg_key_armor'] = unicode(ExpiredKey.__doc__)
        self.receiver_only_update['gpg_key_remove'] = False
        handler = self.request(self.receiver_only_update, role='receiver', user_id=self.dummyReceiver['receiver_gus'])
        yield handler.put()
        self.assertEqual(self.responses[0]['gpg_key_fingerprint'],
            u'C6DAF5B34D5960883C7A9552AACA3A01C2752D4B')

        # ok, now has been imported the key, but we can't perform encryption
        body = ''.join(unichr(x) for x in range(0x370, 0x3FF))
        fake_serialized_receiver = {
            'gpg_key_armor': unicode(ExpiredKey.__doc__),
            'gpg_key_fingerprint': self.responses[0]['gpg_key_fingerprint'],
            'username': u'fake@username.net',
        }
        gpob = GLBGPG(fake_serialized_receiver)
        self.assertTrue(gpob.validate_key(DeveloperKey.__doc__))
        self.assertRaises(errors.GPGKeyInvalid, gpob.encrypt_message, body)

    @inlineCallbacks
    def test_submission_file_delivery_gpg(self):

        new_context = dict(MockDict().dummyContext)
        new_context['name'] = "this uniqueness is no more checked due to the lang"
        new_context_output = yield create_context(new_context)
        self.context_assertion(new_context, new_context_output)

        doubletest = yield get_context_list('en')
        self.assertEqual(len(doubletest), 2)

        yanr = dict(MockDict().dummyReceiver)
        yanr['name'] = yanr['mail_address'] = "quercia@nana.ptg"
        yanr['gpg_key_armor'] = unicode(DeveloperKey.__doc__)
        yanr['gpg_enable_files'] = True
        yanr['contexts'] = [ new_context_output['context_gus']]
        yanr_output = yield create_receiver(yanr)
        self.receiver_assertion(yanr, yanr_output)

        asdr = dict(MockDict().dummyReceiver)
        asdr['name'] = asdr['mail_address'] = "nocibo@rocco.tnc"
        asdr['gpg_key_armor'] = unicode(DeveloperKey.__doc__)
        asdr['gpg_enable_files'] = True
        asdr['contexts'] = [ new_context_output['context_gus']]
        asdr_output = yield create_receiver(asdr)
        self.receiver_assertion(asdr, asdr_output)

        new_subm = dict(MockDict().dummySubmission)
        new_subm['finalize'] = False
        new_subm['context_gus'] = new_context_output['context_gus']
        new_subm['receivers'] = [ asdr_output['receiver_gus'],
                                  yanr_output['receiver_gus'] ]
        new_subm_output = yield create_submission(new_subm, False)
        # self.submission_assertion(new_subm, new_subm_output)

        new_file = dict(MockDict().dummyFile)

        (relationship1, cksum, fsize) = yield threads.deferToThread(files.dump_file_fs, new_file)
        # encrypted output is always greater than the not encrypted
        self.assertGreater(fsize, new_file['body_len'])

        self.registered_file1 = yield files.register_file_db(
            new_file, relationship1, cksum, new_subm_output['submission_gus'] )

        new_subm['submission_gus'] = new_subm_output['submission_gus']
        new_subm['finalize'] = True
        new_subm_output = yield update_submission(new_subm['submission_gus'], new_subm, True)

        yield APSDelivery().operation()

        # now get a lots of receivertips/receiverfiles and check!
        ifilist = yield get_files_by_itip(new_subm_output['submission_gus'])

        self.assertTrue(isinstance(ifilist, list))
        self.assertEqual(len(ifilist), 1)
        self.assertEqual(ifilist[0]['mark'], u'delivered')

        rfilist = yield get_receiverfile_by_itip(new_subm_output['submission_gus'])

        self.assertTrue(isinstance(ifilist, list))
        self.assertEqual(len(rfilist), 2)
        self.assertLess(ifilist[0]['size'], rfilist[0]['size'])
        self.assertLess(ifilist[0]['size'], rfilist[1]['size'])
        self.assertEqual(rfilist[0]['status'], u"encrypted" )
        # completed in love! http://www.youtube.com/watch?v=CqLAwt8T3Ps

        # TODO checks the lacking of the plaintext file!, then would be completed in absolute love



#    @inlineCallbacks
#    def test_invalid_duplicated_key(self):
#
#        self.receiver_only_update = dict(MockDict().dummyReceiver)
#        self.receiver_only_update['gpg_key_armor'] = unicode(DeveloperKey.__doc__)
#        self.receiver_only_update['gpg_key_status'] = None # Test, this field is ignored and set
#        self.receiver_only_update['gpg_key_remove'] = False
#        handler = self.request(self.receiver_only_update, role='receiver', user_id=self.dummyReceiver['receiver_gus'])
#        yield handler.put()
#        self.assertEqual(self.responses[0]['gpg_key_fingerprint'],
#            u'C1ED5C8FDB6A1C74A807569591EC9BB8D9A950DE')
#        self.assertEqual(self.responses[0]['gpg_key_status'], Receiver._gpg_types[1])
#
#        # second receiver creation!
#        new_receiver = dict(MockDict().dummyReceiver)
#        new_receiver['name'] = new_receiver['username'] = \
#            new_receiver['mail_address'] = "quercia@nana.ptg"
#        new_receiver_output = yield create_receiver(new_receiver)
#
#        self.assertGreater(new_receiver_output['receiver_gus'], 10)
#        self.assertNotEqual(self.dummyReceiver['receiver_gus'], new_receiver_output['receiver_gus'])
#
#        handler = self.request(self.receiver_only_update, role='receiver', user_id=new_receiver_output['receiver_gus'])
#        try:
#            yield handler.put()
#            self.assertTrue(False)
#        except
#        except Exception as excep:


    def test_expiration_checks(self):

        keylist = [ HermesGlobaleaksKey.__doc__, DeveloperKey.__doc__, ExpiredKey.__doc__ ]

        expiration_list = get_expirations(keylist)

        today_dt = datetime.date.today()

        for keyid, sincepoch in expiration_list.iteritems():

            expiration_dt = datetime.datetime.utcfromtimestamp(int(sincepoch)).date()

            # simply, all the keys here are expired
            if expiration_dt < today_dt:
                continue

            self.assertTrue(False)
        self.assertTrue(True)



class HermesGlobaleaksKey:
    """
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1.4.11 (GNU/Linux)

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
OawA2tHlxKsF+0YpVn8cBOREJaAgogw5E+AbfqG+WKwWG6WZr8kFHQ0CH2bjUWC2
PMVbYDGyMqCreN5DfmB+rR1an1YS0YqJo+OF1KBULq5KU/vZoD0xUIBBBCCZ20/d
48OT8tRK5S4q0Xo+8nh4tD5HbG9iYUxlYWtzIChodHRwczovL3d3dy5nbG9iYWxl
YWtzLm9yZy8pIDxpbmZvQGdsb2JhbGVha3Mub3JnPokCPgQTAQIAKAIbLwYLCQgH
AwIGFQgCCQoLBBYCAwECHgECF4AFAlGnHgcFCQRtBQwACgkQg5td7QBQs8FqFRAA
u7QZl3SqoKq6uQ5Huh+Z/05yJ/SZCzXpbLjcI+rbQvzwk7+p2ez7DjDquaL+TcI/
hDjsxOWgweQZ+rI9ngzlFwAKK6+FIxZT5nfH6IXRwaTkQWNL2VMEcm0vvQ4t0Nap
eg6gQ5O8gHEVo49BnGsaICqfiD8YSk1Iz8vP3xwxx+KyYIkem2sz6XEOtpXODlp9
fMu4TzM0ofIzqjdNK1kutniKVXzPgfll8tXgrnaG56qjL7CvQUnAIufMfFPPUWiW
BRHI6jDB7VYHfmbD021qLTA3mTl3YsZepnG7sDhEPmiVmI6x2x+S1ExegcsTfs0q
42A6mUhT8imkAxoInOG7MaWs3ER/oVeCw2U+2uhusQ06W/0+1pKum/W9SKhfXHMc
oSw6w3siudBK8afFdMDfB6GYbS/hbLiieklljRv1ij70y+rKqYPXjiSo2jO4gXhI
XaX1+PzP/k+rYIa59GI437RQn0GO4eJF65U7P8Bz7sLUaya/nngul6VY3dhmAGze
2gk+9axMWvBfDOGe6s0IDKQsxFrd69cA2bOOsVEhpvyiHW28ylx/Ni11VVqKTUsy
ncRoatiQO7PSk6Qdk/jSyN6P9Ly9fqMk/j4MqVkdQxr16h7q0K6dGJt5dWIVnBWK
os8FoIi4v49E5+LZSQzVsShTMAweAnRZ46sItPUhroaIRgQQEQIABgUCTyJg0wAK
CRC4Qgk9xnZUMIcLAJ9pSib2QPWB6wqCAONe0X3NGWbtWACgtJ+Ya8SJkYceR/2r
x17Tr/kyPyyIRgQQEQIABgUCTymJogAKCRAkgE95gKtvMUCyAJ4hkb5JZjh7THHT
YiVHWuQ8qVN4DgCgotiFyw4gG/jrsdolhRbM7gb5sUyIRgQQEQIABgUCTxtOOQAK
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
71FdYqP5qSLo6/Xs/iA0dPaGXyE9
=0Iga
-----END PGP PUBLIC KEY BLOCK-----
    """
    pass

class DeveloperKey:
    """
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1.4.11 (GNU/Linux)

mQGiBEoHECwRBACDiq9qi2gtsehmK1AffXyXHD6f3eQ2YCMxGzdFmvfCnt6k2qFC
FCx44GDlolkeeWb8nRWMOYkHeRzAqbAubB059ufxNo04XXjdVVztmxQYZ+5JbOzu
k4NorCs0m9IG6djAbB5pmJA48hNM5cmP3KtoJURwzts8oYutoTap5Sj/4wCgl1Xw
OUueV+o6/5sJ2km+HOqgP08D/A7fqPqFqx8b2MUmIt1v6olxsOyg1ArZgcmAxYfc
ew3CMSgDJc9GdP4mMne2sqAD7wZ1THjAIBYggeg1wJWfmFOlA/do5nsoKBpuL67q
kLSjf8Hp5kYYqZnM2OEygTWGRYvbwvTMdJiCokHMW/S1IyqSKuatVV+1zFNmtcZi
r+EdA/oC6G+Gl65EJv0/2q/iEQypwsXrI9lhMOfoZiWgLI/utmtJP7K2Y3u+8VTG
rEbIEj7R5p26ssPCxNy+XhchIktuZeMaenbkSmEsHeeUGCoX3adbMR6fYTctEWpP
ti8OvxNkvrIwsxTSAbtM6Jv7SdJkvSWcfk6i+X33EP9IdrD+eLRBR2lvdmFubmkg
J2V2aWxhbGl2MycgUGVsbGVyYW5vIDxnaW92YW5uaS5wZWxsZXJhbm9AZXZpbGFs
aXYzLm9yZz6IawQTEQIAKwIbAwYLCQgHAwIGFQgCCQoLBBYCAwECHgECF4ACGQEF
AlFZX6QFCQsUtnIACgkQkeybuNmpUN73TgCfZlkI4ao1ywV7QR3Xx2+Y88BgNsgA
ninRQUukeLSC3H852TAJv1wxQ3wBtDlHaW92YW5uaSAnZXZpbGFsaXYzJyBQZWxs
ZXJhbm8gPGV2aWxhbGl2M0BnbG9iYWxlYWtzLm9yZz6IaAQTEQIAKAIbAwYLCQgH
AwIGFQgCCQoLBBYCAwECHgECF4AFAlFZX6QFCQsUtnIACgkQkeybuNmpUN7CIwCg
gOkYHS/VLxNnzqYA/S+TRaXy4BUAnjF6Dd/jau7/IwL97F+AJ9Dwfu3TtERHaW92
YW5uaSAnZXZpbGFsaXYzJyBQZWxsZXJhbm8gPGdpb3Zhbm5pLnBlbGxlcmFub0Bs
b2dpb3NoZXJtZXMub3JnPohoBBMRAgAoAhsDBgsJCAcDAgYVCAIJCgsEFgIDAQIe
AQIXgAUCUVlfpAUJCxS2cgAKCRCR7Ju42alQ3hWoAJ96OJm89VSMdIIpW9dXyyOk
nXiiRACghz9pWkMUAM0/vAmdBMqPbsqQzk25BA0ESgcQLBAQAKgkGO7el8NgAaX+
ksA7zMFz7+03vVMB/FQ7gllPU9rS7QoawsOsAEKKGQvvyhT6KFvAU4ut/07zpVjQ
x9bPoyreE6v7IMa48WQTG9cEwrWqapYryNBxKju8XYApkhV46vEnHgH3E+Zut3XH
LihT8/vyVrfv2Hxe0q1wbuizCGRMOgRZ5Ktn5ZPwazfp9lAyfBCApzmKdzIxIJ3u
rdoDU/sNMJvX334/mS+xReDngYc5cQJ9tA2IWHo8GtrOQGM5D/hMfXmClSfdRG3P
jpxVvLMV7hxeQzSlSu0Z9UUSC33nuhWfUtazSvUR7uEF9GVYrDYjOiTI0aaunIdo
E8V+4g2+nyoPBKUA7psiJSaWgjITkmNtX+n7JVoCtsRCCOb5tFe31p4n061Cd9V5
6ME2U2mK/TxAZ4/Czr1ocJG2M3mlUgmky6aLKQIcWLLrca8z2Gem8Ef9tx6/j90f
FyS+MFlIGohkCFN1AzpcWY2w7F7RmvewYFqZHH3hk+VP+xI4xCAMx84wEmcVd4XW
Sam/edcGOTsVnZOj44ePgirQjuws+SlPC4z34xGsoZpT2fBudHG92gdb8TRbXGM2
5IUAsSLSllI/oq+yE3V+Hj2Hz/rCWFNVkViOcguIA9TYmXclCvGxlVEk18oyeE7h
ZOBSE5uWII2U5JYkTwVN4oJO3wmbAAMFD/9qi/91xyRCmltKy6Pb51I69WZNrOwq
YYYG3wuNH7DcSA/+7nTcH5WPFeiGZYB2QD9/nC1Sv0RxmnuMasU53fbgrf8+oqwF
8VuYQ0lmz2clxCl7WyqF2hrCg6gsXwcOw3rkxb4bkt/p17FXQZ1vZaSa9cr3hSZD
ZqJ+LsMrvof0zyl3sTE7CdXF0uHLHhBaYeRLQGsOr+pUu09kjuAf68ksDCEPhIE5
WvhR1Esi29OZMBhwyQMWlbh+hij5OiJnMV+dvN1NqG8TYO/bcpc51EfSY46lTzVX
mUVZylUXDV7+Ghp9OETBWm8Tc1RCDLvTdPkJeybmkPb3cQYstgL/vx0CWpvkNAt3
nLozDH43Ep34+su7QINDZ+uYwLvcHvkToceGghZu1uGlg2nuCwFz7Xxw1TKw0pPU
MPvEgd30udNoVL80C4iv42V5NAo6eNvrKr7evzL3F+tM/uegDb9ffNtcEYK1uiCN
3jp/dukLnV3pvFRswAYHHUkw1hSXFq3AiVzbxY6YCAYpBk6v96kRtPePr5RnfNxq
lCd8yu/YnOwc4P+Xt7dYCJYRDEds209RNtujAl+dDTnW7zR0p8mycNyB9PdMhuoA
ajPgbCSvefQhxSkKTCKuoO77iPaTZsNIWBqh9pzcR8rmFAdRGBCWVKtpTcLiZn/j
9wQjtv8VJWDWu4hPBBgRAgAPAhsMBQJRWV/PBQkLFLafAAoJEJHsm7jZqVDegZoA
nRDMINePXcFzxkdVHgKpzUrXlfrBAKCSUbYHucAwQ3LKcjc2AGpUL51RGA==
=BATO
-----END PGP PUBLIC KEY BLOCK-----
    """
    pass

class ExpiredKey:
    """
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1.4.11 (GNU/Linux)

mQGiBDmAu40RBAD13RF3ugwdmi+NdD7OeIhxHZVEN7wdTdYvksiX8CTzY0mpMGNA
JcRg2llQGddQ+vtEy4W+LVsreL3STbjNXx4n9ttrCvCtKUukxIF9iN5shSvOJqVJ
VvzLlqYIjYADVtWLlyLEZp67bKIB2wPuCX+5YnqNer+T8u2hip66tnVbEwCgwt8P
yZ5K4xqyIY1fxOH2M5YKxmcEAKsJ3l1wv1Zr3xzAi5k3ysY8bkiSjgV/AQ3FVKwc
iqjXx60PPSuzSLk2h7pspSpr8v3z7yuMi0w/+a+BcNNPMpZxv3CDtY2fVWfPbIJ4
T8pm9kiIyxc20tgbSwjdGTDIDlygz+EMAE4OB6XlzGJJLO448G7K38f4L2y+QMHu
GRdqBADObnvxMZRMzFrTjwryulPHYsxWnnRrHKlVnkw4AI+rp7IzeT39+OJxEpjb
U1xMvd269CW4cvu4RFHbYFy58DDDmbq1ibeksgRJtrBc08+c6X0at1Q6HJRzbcpt
r3ZYmfF78pTMzrzqy8DrKCdpbieIStCL0T3ChkAJupVwSTlfFojlBCARAgClBQJG
3lfdnh0BSSd2ZSBnZW5lcmF0ZWQgYSBuZXcga2V5LCBzaWduZWQgd2l0aCB0aGlz
IG9sZCBvbmUuIHRoZSBuZXcga2V5IGZpbmdlcnByaW50IGlzIEI5QjYgQUU4QSBG
NEJDIDMyNjEsIHZlY25hIChhdCkgczBmdHBqLm9yZywgd2luc3RvbnNtaXRoLmlu
Zm8sIGRlbGlyYW5kb20ubmV0AAoJEKrKOgHCdS1Llr0AoLtAd4PqWAxTjy3atxpO
IvER3kFsAKCjQ9GWO9+q1mu0E1QouJ4NDTkCDrQYdmVjbmEgPHZlY25hQHMwZnRw
ai5vcmc+iFYEExECABYFAjmAu40ECwoEAwMVAwIDFgIBAheAAAoJEKrKOgHCdS1L
o5YAoKB1yJi4No2kGDcWPwh/G6xde6seAKCXTJ7YZzqs+EZ84gyIB3Owfe1LEYhG
BBARAgAGBQI9OdJGAAoJEOEoOEbl8o3GQwQAnAsh+uTGlNxLfmTDmQfisfuvDksD
AJ0T+1nEkjQcyAw13ruLzdK5JuiASohJBDARAgAJBQI+xVNBAh0AAAoJEOEoOEbl
8o3Ga7oAoIeMJlgFPBQH/ZygOA5V/Or2BSViAKCJC+PirDgdNqjIM8iNwPGxnhbu
johWBBMRAgAWBQI5gLuNBAsKBAMDFQMCAxYCAQIXgAAKCRCqyjoBwnUtS6OWAJ9m
FJ5oh7y1xENE00Ys1fEYMNYqLgCfflmZuzkhr3Dba8+Idm7HisgSJviIRgQTEQIA
BgUCQEh0GAAKCRCV+pdjJ8VJcxc2AKCltDYGBRdFNQN/z8O5TyWbQcCujQCbB0KA
k3jxjLEEosAHFoTn9LEVUAOIRgQTEQIABgUCPTmxEQAKCRBYsILWW25tlyJ4AKC5
jUK165mxKjqv43xXgQzhc1rXxACfTgdy5NxMCn13Bc88Cdf/z3cyf9uIRgQTEQIA
BgUCPSPv/QAKCRAHaiVhHWe03UyaAKCIe9ryDcFMyXtpME/LsZOV6cXEQACfUKcY
OJFOn8XfaLc8kUC1lFQKLbeIRgQQEQIABgUCQWne0wAKCRD8r2UhmngBA6eEAJ9C
mmM4EANkM4AT5VwtaIev39IfdQCfWj+PHdLFqycfGlMfrcxJviPjnumIRgQQEQIA
BgUCQHJweAAKCRB4v95w+cPW8J1VAKDQ1ldbBygvQwr2ddOKY457px64KQCgmHpy
If9RE8izUlymSFSV4crNSWCIRgQQEQIABgUCP3QTlQAKCRCjFjS1H8XbJAA5AKCL
sJA7iq8h7qZ19KtjC//bcMSwTQCgkN3sDh6ELGAq7mLSmEIxO1vzs2uIRgQQEQIA
BgUCPTvhGwAKCRCKzXXXAA93C9L2AJ9nzYsvzERE9QYIh69IRevtspCvwACgtcCk
PaulLQefdCgPASuayYI4v1GIRgQQEQIABgUCPTvfaQAKCRBx4S7Fgxjkwc4MAKDX
agEaI92d27KlLAoELLpiCq4qygCdEIEbVAEtxZfXJc6+hFnrUFzQCryIRgQQEQIA
BgUCPTqCcAAKCRAAHN5qa3nUAQPjAJ9c3hwsq/W4zRYZVkTtXZLd4TDTYgCglmpZ
ilkQjHmf/8hZCTbkYAn5PZ2IRgQQEQIABgUCQuQOHQAKCRAwnyybvaLo/5HKAJwJ
X7yAN5418pyK08ScTvRnH9O6QQCfQLP55a1InBZjNIB/FnRgExfVf3mIRgQQEQIA
BgUCQuQSRwAKCRAEPohYtHb8b+q7AJ0eoyoyFNOgNQA93gEbNjerKm8yWwCeMAcD
p9LsrXuIqbRC4jA9CB6SKO2IRgQQEQIABgUCQ29JvgAKCRB4v95w+cPW8KFlAKCs
kEXHGaksDjRHqO5/PkooOKRCmwCdG3zrETPVax6icrMH4377+S/JjqaIRgQQEQIA
BgUCQ8WHFQAKCRALl/GYH4XBkDnbAJ9TqVrr/xju4H/mm0KMQYbCwzvSpwCgmMHh
0Tzj417eseC2AziFWy16LKOIRgQQEQIABgUCQ8WHFQAKCRALl/GYH4XBkN5UAJ9F
GfKQkQIyZWzsWO3VbfUKpbuPvgCgoQN5snLAbrwNxyJDMYOb3AVBIGyIRgQQEQIA
BgUCRBNcYwAKCRD5ETzOKKh7xyirAJ9hq/g137aCxVdBFAb8FHtc5CAX7wCgt76I
625fl+nMx7H3Kl7Ol4asbeGIRgQQEQIABgUCRBNcZgAKCRD5ETzOKKh7xxI6AJ0d
x3KIiTc7oMNf+MIHG21r9ebKywCgsq4zpi0wqwyuVdqzyPao5e43xryIRgQQEQIA
BgUCQ29JuAAKCRB4v95w+cPW8C36AJwPbTTRSWBh+UPgir+cGqigKlA5xgCghr3C
ZfTcHj5huVBzuV7jJgAEQgiIRgQSEQIABgUCQEjqtAAKCRCAwcupHiLRqQaAAKCH
GPMltRgYnYV4d48Z1LJJVhmOhACg4MXHxqHb8J2DdRqPyekyU3MHqlSIRgQSEQIA
BgUCQEjqvwAKCRCAwcupHiLRqbMBAJsHJ6y/OF0/9NmYEh94/KTHq4w8CACg3833
axbVsgKa0WjbUfFFg/96Sgy0HkNsYXVkaW8gPGNsYXVkaW9AYmxhY2toYXRzLml0
PohGBBARAgAGBQI/dBORAAoJEKMWNLUfxdskiisAoJKNk5EE2+epN1eHSBLi6pHu
+19eAJ40W4gcOm1SPD9GqGO/L982wBnLfohGBBMRAgAGBQJASHQTAAoJEJX6l2Mn
xUlz46wAmQFFVftMH9+bBK6NCSuZ/FzJwxAaAKCygT4JuIu3vzaVdWqECTpEjxXk
IYhGBBARAgAGBQJBad7PAAoJEPyvZSGaeAED0HcAn25RmBms7kp7v+NXcD+AnYUo
8TGoAJ0aNDmL2qRjL6lCyLYta9Yw8UbfDYhGBBARAgAGBQJAcnB4AAoJEHi/3nD5
w9bwH+EAoPqw6Va2G77Y0/UeZ3dGkGzJtdPNAKD25LOkiY6H13Wtz49qDaPSIlyc
O4hGBBARAgAGBQJBPBoQAAoJEAdqJWEdZ7TdQf8AoNK+PE8wSXfEGSkogT299gFm
0UapAKDmK1zmXNdzuSEpkUeaTmUHNcILRIhGBBARAgAGBQJC5A4ZAAoJEDCfLJu9
ouj/3JIAoJygvzE1NYbrkvRgK+MMXPFCdR7PAJ0c8ocjLCbTc5VrLLqs680JGjpa
J4hGBBARAgAGBQJC5BJEAAoJEAQ+iFi0dvxvYdkAnRM0koInnurv1uQk/EzByYFs
h5CoAJ9pFIKU0ge2MzkvnMx0xMobN5XEOohGBBARAgAGBQJDb0m4AAoJEHi/3nD5
w9bwLfoAnA9tNNFJYGH5Q+CKv5waqKAqUDnGAKCGvcJl9NwePmG5UHO5XuMmAARC
CIhGBBARAgAGBQJDxYcVAAoJEAuX8ZgfhcGQ3lQAn0UZ8pCRAjJlbOxY7dVt9Qql
u4++AKChA3mycsBuvA3HIkMxg5vcBUEgbIhGBBARAgAGBQJEE1xjAAoJEPkRPM4o
qHvHKKsAn2Gr+DXftoLFV0EUBvwUe1zkIBfvAKC3vojrbl+X6czHsfcqXs6Xhqxt
4YhXBBMRAgAXBQI9+8whBQsHCgMEAxUDAgMWAgECF4AACgkQqso6AcJ1LUvYXACf
U42gptOsvt3La0nz7o/oeg4zPVkAoKffMPvSUgaadq/lzvrd44Cd+0+DiEYEEhEC
AAYFAkBI6rQACgkQgMHLqR4i0akGgACghxjzJbUYGJ2FeHePGdSySVYZjoQAoODF
x8ah2/Cdg3Uaj8npMlNzB6pUuQINBDmAvB4QCADAjMKYPJLuzl9mA3AL2zdfhqxU
gUiCyX68yJznJ+WgXxTa66Ctd26mfMTNuJzf9ZKsienhLo0HY4KX9yreTLYaIDgu
lGYARHEew1YycGFeN9JWTlTnYC8hE3/zxPTb03GYaqNMPaxXhh73q7AAhLpWdPaU
qGKYgh1usf5Me966/azlASNOHJes6qVZD794FbMPxQb9ZktqeYT+AnhkLywXyIw4
Cn8MW/4mdl8NsmMX0h9KNmwT2hzoJW/hovNFtJBeNoimVUbZlupLTReyYPJ5tT5T
KW8hRkX3zhTolCDRlLen8SXJa/z0LMgcanWnClp4GTHgmXdvtGLf/OUOch8jAAMF
B/sHLIwiMv9fk2/zNjcHhquIoU0IdQaP2v2GLWSFHtM4L8qr8Ie7yECE3Gntj5cQ
ByE4Z4UmhiEQ17xhAVDNdKUOMPYiR/TJPWA4C3KoyHmHm0jMfPCOg9/gy93Ntgq0
dnIuMWkCLf7y3bFL/2NgoQFrbeNc+f5JmTybIUTZ9C1Z1N24t4FaRt1OxdehtZWr
EwXgWFMD7lHnl1s+RXY1pOLu8Pr0aI88KddTtkGOXGu4uAEXFqkbJsq4BRhwszKx
CxY7JrT/nnBlKfniHLrdncxBGWYy0aNFRPVoP6TnivYl/lxbpqxyHzA9S7hPRbCn
SFn8QEUQapXCudtgmOmiVxeNiEYEGBECAAYFAjmAvB4ACgkQqso6AcJ1LUv66QCe
P9QCMWw+aewWapGlXn5IyKLtSXUAn17BSPupIxdA/V6AEQHtSMcnYfO7
=SJOc
-----END PGP PUBLIC KEY BLOCK-----
    """
    pass
