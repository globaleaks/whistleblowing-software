# -*- encoding: utf-8 -*-

import os
import datetime

from twisted.internet import threads
from twisted.internet.defer import inlineCallbacks

from globaleaks.rest import errors
from globaleaks.security import GLBGPG, get_expirations
from globaleaks.handlers import receiver, files
from globaleaks.handlers.admin import create_receiver, create_context, get_context_list, get_context_fields
from globaleaks.handlers.submission import create_submission, update_submission
from globaleaks.settings import GLSetting
from globaleaks.models import Receiver
from globaleaks.jobs.delivery_sched import DeliverySchedule, get_files_by_itip, get_receiverfile_by_itip
from globaleaks.plugins.notification import MailNotification
from globaleaks.plugins.base import Event
from globaleaks.utils.templating import Templating

from globaleaks.tests.helpers import MockDict, fill_random_fields, TestHandlerWithPopulatedDB, VALID_PGP_KEY

GPGROOT = os.path.join(os.getcwd(), "testing_dir", "gnupg")

class TestReceiverSetKey(TestHandlerWithPopulatedDB):
    _handler = receiver.ReceiverInstance

    receiver_desc = {
        'username': 'evilaliv3@useless_information_on_this_test.org',
        'name': 'assertion',
        'gpg_key_fingerprint': 'CF4A22020873A76D1DCB68D32B25551568E49345',
        'gpg_key_status': Receiver._gpg_types[1] }

    receiver_only_update = {
        'gpg_key_armor': None, 'gpg_key_remove': False,
        "gpg_key_info": None, "gpg_key_fingerprint": None,
        'gpg_key_status': Receiver._gpg_types[0], # Disabled
        "gpg_enable_notification": False,
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

        handler = self.request(self.dummyReceiver_1, role='receiver', user_id=self.dummyReceiver_1['id'])
        yield handler.get()
        self.assertEqual(self.responses[0]['gpg_key_info'], None)

    @inlineCallbacks
    def test_default_encryption_enable(self):

        self.receiver_only_update = dict(MockDict().dummyReceiver)

        self.receiver_only_update['password'] = self.dummyReceiver_1['password']
        self.receiver_only_update['old_password'] = self.dummyReceiver_1['password']
        self.receiver_only_update['gpg_key_armor'] = unicode(VALID_PGP_KEY)
        self.receiver_only_update['gpg_key_status'] = None # Test, this field is ignored and set
        self.receiver_only_update['gpg_key_remove'] = False
        handler = self.request(self.receiver_only_update, role='receiver', user_id=self.dummyReceiver_1['id'])
        yield handler.put()
        self.assertEqual(self.responses[0]['gpg_key_fingerprint'],
                         u'CF4A22020873A76D1DCB68D32B25551568E49345')
        self.assertEqual(self.responses[0]['gpg_key_status'], Receiver._gpg_types[1])

        self.receiver_only_update['gpg_key_armor'] = unicode(HermesGlobaleaksKey.__doc__)
        self.assertEqual(self.responses[0]['gpg_enable_notification'], True)

    @inlineCallbacks
    def test_handler_update_key(self):

        self.receiver_only_update = dict(MockDict().dummyReceiver)

        self.receiver_only_update['password'] = self.dummyReceiver_1['password']
        self.receiver_only_update['old_password'] = self.dummyReceiver_1['password']
        self.receiver_only_update['gpg_key_armor'] = unicode(VALID_PGP_KEY)
        self.receiver_only_update['gpg_key_status'] = None # Test, this field is ignored and set
        self.receiver_only_update['gpg_key_remove'] = False
        handler = self.request(self.receiver_only_update, role='receiver', user_id=self.dummyReceiver_1['id'])
        yield handler.put()
        self.assertEqual(self.responses[0]['gpg_key_fingerprint'],
            u'CF4A22020873A76D1DCB68D32B25551568E49345')
        self.assertEqual(self.responses[0]['gpg_key_status'], Receiver._gpg_types[1])

        self.receiver_only_update['gpg_key_armor'] = unicode(HermesGlobaleaksKey.__doc__)
        self.receiver_only_update['gpg_key_remove'] = False
        handler = self.request(self.receiver_only_update, role='receiver', user_id=self.dummyReceiver_1['id'])
        yield handler.put()
        self.assertEqual(self.responses[1]['gpg_key_fingerprint'],
            u'12CB52E0D793A11CAF0360F8839B5DED0050B3C1')
        # and the key has been updated!

    @inlineCallbacks
    def test_transact_malformed_key(self):
        self.receiver_only_update['password'] = self.dummyReceiver_1['password']
        self.receiver_only_update['old_password'] = self.dummyReceiver_1['password']
        self.receiver_only_update['gpg_key_armor'] = unicode(VALID_PGP_KEY).replace('A', 'B')
        self.receiver_only_update['gpg_key_status'] = None # Test, this field is ignored and set
        self.receiver_only_update['gpg_key_remove'] = False
        handler = self.request(self.receiver_only_update, role='receiver', user_id=self.dummyReceiver_1['id'])
        yield self.assertFailure(handler.put(), errors.GPGKeyInvalid)

    def test_Class_encryption_message(self):

        dummy_template = { "en" : "In %EventTime% you've got a crush for Taryn Southern, yay!!"
                            "more info on: https://www.youtube.com/watch?v=C7JZ4F3zJdY "
                            "and know that you're not alone!" }

        mock_event = Event(type=u'encrypted_tip', trigger='Tip',
                    notification_settings = dummy_template,
                    trigger_info = {
                        'creation_date': '2013-05-13T17:49:26.105485', #epoch!
                        'id': 'useless',
                        'wb_steps' : fill_random_fields(self.dummyContext['id']),
                    },
                    node_info = MockDict().dummyNode,
                    receiver_info = MockDict().dummyReceiver,
                    context_info = MockDict().dummyContext,
                    steps_info = {},
                    plugin = MailNotification(),
                    trigger_parent = {} )

        mail_content = Templating().format_template(dummy_template, mock_event)

        # setup the GPG key before
        GLSetting.gpgroot = GPGROOT

        fake_receiver_desc = {
            'gpg_key_armor': unicode(VALID_PGP_KEY),
            'gpg_key_fingerprint': u"CF4A22020873A76D1DCB68D32B25551568E49345",
            'gpg_key_status': Receiver._gpg_types[1],
            'username': u'fake@username.net',
        }

        gpob = GLBGPG(fake_receiver_desc)
        self.assertTrue(gpob.validate_key(VALID_PGP_KEY))

        encrypted_body = gpob.encrypt_message(mail_content)
        self.assertSubstring('-----BEGIN PGP MESSAGE-----', encrypted_body)

    def test_Class_encryption_file(self):

        # setup the GPG key before
        GLSetting.gpgroot = GPGROOT

        tempsource = os.path.join(os.getcwd(), "temp_source.txt")
        with file(tempsource, 'w+') as f1:
            f1.write("\n\nDecrypt the Cat!\n\nhttp://tobtu.com/decryptocat.php\n\n")

            f1.seek(0)

            fake_receiver_desc = {
                'gpg_key_armor': unicode(VALID_PGP_KEY),
                'gpg_key_status': Receiver._gpg_types[1],
                'gpg_key_fingerprint': u"CF4A22020873A76D1DCB68D32B25551568E49345",
                'username': u'fake@username.net',
                }

            # these are the same lines used in delivery_sched.py
            gpoj = GLBGPG(fake_receiver_desc)
            gpoj.validate_key(VALID_PGP_KEY)
            encrypted_file_path, encrypted_file_size = gpoj.encrypt_file(tempsource, f1, "/tmp")
            gpoj.destroy_environment()

            with file(encrypted_file_path, "r") as f2:
                first_line = f2.readline()

            self.assertSubstring('-----BEGIN PGP MESSAGE-----', first_line)

            with file(encrypted_file_path, "r") as f2:
                whole = f2.read()
            self.assertEqual(encrypted_file_size, len(whole))

    @inlineCallbacks
    def test_expired_key_error(self):

        self.receiver_only_update['gpg_key_armor'] = unicode(ExpiredKey.__doc__)
        self.receiver_only_update['gpg_key_remove'] = False
        handler = self.request(self.receiver_only_update, role='receiver', user_id=self.dummyReceiver_1['id'])
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
        self.assertTrue(gpob.validate_key(VALID_PGP_KEY))
        self.assertRaises(errors.GPGKeyInvalid, gpob.encrypt_message, body)

    @inlineCallbacks
    def test_submission_file_delivery_gpg(self):

        new_fields = MockDict().dummyFields
        new_context = MockDict().dummyContext

        # the test context need fields to be present
        from globaleaks.handlers.admin.field import create_field
        for idx, field in enumerate(self.dummyFields):
            f = yield create_field(field, 'en')
            new_fields[idx]['id'] = f['id']

        new_context['steps'][0]['children'] = [
            new_fields[0]['id'], # Field 1
            new_fields[1]['id'], # Field 2
            new_fields[4]['id']  # Generalities
        ]

        new_context['name'] = "this uniqueness is no more checked due to the lang"
        new_context_output = yield create_context(new_context)
        self.context_assertion(new_context, new_context_output)

        doubletest = yield get_context_list('en')
        self.assertEqual(len(doubletest), 2)

        yanr = dict(MockDict().dummyReceiver)
        yanr['name'] = yanr['mail_address'] = u"quercia@nana.ptg"
        yanr['gpg_key_armor'] = unicode(VALID_PGP_KEY)
        yanr['contexts'] = [ new_context_output['id']]
        yanr_output = yield create_receiver(yanr)
        self.receiver_assertion(yanr, yanr_output)

        asdr = dict(MockDict().dummyReceiver)
        asdr['name'] = asdr['mail_address'] = u"nocibo@rocco.tnc"
        asdr['gpg_key_armor'] = unicode(VALID_PGP_KEY)
        asdr['contexts'] = [ new_context_output['id']]
        asdr_output = yield create_receiver(asdr)
        self.receiver_assertion(asdr, asdr_output)

        new_subm = dict(MockDict().dummySubmission)

        new_subm['finalize'] = False

        new_subm['context_id'] = new_context_output['id']
        new_subm['receivers'] = [ asdr_output['id'],
                                  yanr_output['id'] ]
        new_subm['wb_steps'] = yield fill_random_fields(new_context_output)
        new_subm_output = yield create_submission(new_subm, False)
        # self.submission_assertion(new_subm, new_subm_output)

        self.emulate_file_upload(new_subm_output['id'])

        new_file = self.get_dummy_file()

        new_subm['id'] = new_subm_output['id']
        new_subm['finalize'] = True
        new_subm_output = yield update_submission(new_subm['id'], new_subm, True)

        yield DeliverySchedule().operation()

        # now get a lots of receivertips/receiverfiles and check!
        ifilist = yield get_files_by_itip(new_subm_output['id'])

        self.assertTrue(isinstance(ifilist, list))
        self.assertEqual(len(ifilist), 2)
        self.assertEqual(ifilist[0]['mark'], u'delivered')

        rfilist = yield get_receiverfile_by_itip(new_subm_output['id'])

        self.assertTrue(isinstance(ifilist, list))
        self.assertEqual(len(rfilist), 2)

        for i in range(0, 2):
            self.assertLess(ifilist[0]['size'], rfilist[i]['size'])

        self.assertEqual(rfilist[0]['status'], u"encrypted" )
        # completed in love! http://www.youtube.com/watch?v=CqLAwt8T3Ps

        # TODO checks the lacking of the plaintext file!, then would be completed in absolute love

    def test_expiration_checks(self):

        keylist = [ HermesGlobaleaksKey.__doc__, VALID_PGP_KEY, ExpiredKey.__doc__ ]

        expiration_list = get_expirations(keylist)

        today_dt = datetime.date.today()

        for keyid, sincepoch in expiration_list.iteritems():

            expiration_dt = datetime.datetime.utcfromtimestamp(int(sincepoch)).date()

            # simply, all the keys here are expired
            self.assertTrue(expiration_dt < today_dt)


class HermesGlobaleaksKey:
    """
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1

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
vNbv//uY5eBSTsv95WflQQ==
=+Rtw
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
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
=SJOc
-----END PGP PUBLIC KEY BLOCK-----
    """
    pass
