# -*- encoding: utf-8 -*-

import os

from datetime import datetime

from twisted.internet import threads
from twisted.internet.defer import inlineCallbacks

from globaleaks.rest import errors
from globaleaks.security import GLBGPG
from globaleaks.handlers import receiver, files
from globaleaks.handlers.admin import create_receiver, create_context, get_context_list
from globaleaks.handlers.submission import create_submission, update_submission
from globaleaks.settings import GLSetting
from globaleaks.models import Receiver
from globaleaks.jobs.delivery_sched import DeliverySchedule, get_files_by_itip, get_receiverfile_by_itip
from globaleaks.plugins.base import Event
from globaleaks.utils.templating import Templating

from globaleaks.tests.helpers import MockDict, fill_random_fields, TestHandlerWithPopulatedDB, VALID_PGP_KEY1, VALID_PGP_KEY2, EXPIRED_PGP_KEY

GPGROOT = os.path.join(os.getcwd(), "testing_dir", "gnupg")

class TestGPG(TestHandlerWithPopulatedDB):
    _handler = receiver.ReceiverInstance

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
        self.receiver_only_update['gpg_key_armor'] = unicode(VALID_PGP_KEY1)
        self.receiver_only_update['gpg_key_status'] = None # Test, this field is ignored and set
        self.receiver_only_update['gpg_key_remove'] = False
        handler = self.request(self.receiver_only_update, role='receiver', user_id=self.dummyReceiver_1['id'])
        yield handler.put()
        self.assertEqual(self.responses[0]['gpg_key_fingerprint'],
                         u'CF4A22020873A76D1DCB68D32B25551568E49345')
        self.assertEqual(self.responses[0]['gpg_key_status'], u'enabled')

        self.receiver_only_update['gpg_key_armor'] = unicode(VALID_PGP_KEY2)

    @inlineCallbacks
    def test_handler_update_key(self):
        self.receiver_only_update = dict(MockDict().dummyReceiver)

        self.receiver_only_update['password'] = self.dummyReceiver_1['password']
        self.receiver_only_update['old_password'] = self.dummyReceiver_1['password']
        self.receiver_only_update['gpg_key_armor'] = unicode(VALID_PGP_KEY1)
        self.receiver_only_update['gpg_key_status'] = None # Test, this field is ignored and set
        self.receiver_only_update['gpg_key_remove'] = False
        handler = self.request(self.receiver_only_update, role='receiver', user_id=self.dummyReceiver_1['id'])
        yield handler.put()
        self.assertEqual(self.responses[0]['gpg_key_fingerprint'],
            u'CF4A22020873A76D1DCB68D32B25551568E49345')
        self.assertEqual(self.responses[0]['gpg_key_status'], u'enabled')

        self.receiver_only_update['gpg_key_armor'] = unicode(VALID_PGP_KEY2)
        self.receiver_only_update['gpg_key_remove'] = False
        handler = self.request(self.receiver_only_update, role='receiver', user_id=self.dummyReceiver_1['id'])
        yield handler.put()
        self.assertEqual(self.responses[1]['gpg_key_fingerprint'],
            u'7106D296DA80BCF21A3D93056097CE44FED083C9')
        # and the key has been updated!

    @inlineCallbacks
    def test_load_malformed_key(self):
        self.receiver_only_update = dict(MockDict().dummyReceiver)

        self.receiver_only_update['password'] = self.dummyReceiver_1['password']
        self.receiver_only_update['old_password'] = self.dummyReceiver_1['password']
        self.receiver_only_update['gpg_key_armor'] = unicode(VALID_PGP_KEY1).replace('A', 'B')
        self.receiver_only_update['gpg_key_status'] = None # Test, this field is ignored and set
        self.receiver_only_update['gpg_key_remove'] = False
        handler = self.request(self.receiver_only_update, role='receiver', user_id=self.dummyReceiver_1['id'])
        yield self.assertFailure(handler.put(), errors.GPGKeyInvalid)

    def test_encrypt_message(self):

        dummy_template = "In %EventTime% you've got a crush for Taryn Southern, yay!! \
                         more info on: https://www.youtube.com/watch?v=C7JZ4F3zJdY \
                         and know that you're not alone!"

        mock_event = Event(type=u'encrypted_tip',
                           trigger='Tip',
                           tip_info = {
                               'creation_date': '2013-05-13T17:49:26.105485', #epoch!
                               'id': 'useless',
                               'wb_steps' : fill_random_fields(self.dummyContext['id']),
                           },
                           node_info = MockDict().dummyNode,
                           receiver_info = MockDict().dummyReceiver,
                           context_info = MockDict().dummyContext,
                           steps_info = {},
                           subevent_info = {},
                           do_mail=False)

        mail_content = Templating().format_template(dummy_template, mock_event)

        # setup the GPG key before
        GLSetting.gpgroot = GPGROOT

        fake_receiver_desc = {
            'gpg_key_armor': unicode(VALID_PGP_KEY1),
            'gpg_key_fingerprint': u"CF4A22020873A76D1DCB68D32B25551568E49345",
            'gpg_key_status': u'enabled',
            'username': u'fake@username.net',
        }

        gpgobj = GLBGPG()
        gpgobj.load_key(VALID_PGP_KEY1)

        encrypted_body = gpgobj.encrypt_message(fake_receiver_desc['gpg_key_fingerprint'], mail_content)
        self.assertSubstring('-----BEGIN PGP MESSAGE-----', encrypted_body)

        gpgobj.destroy_environment()

    def test_encrypt_file(self):

        # setup the GPG key before
        GLSetting.gpgroot = GPGROOT

        tempsource = os.path.join(os.getcwd(), "temp_source.txt")
        with file(tempsource, 'w+') as f1:
            f1.write("\n\nDecrypt the Cat!\n\nhttp://tobtu.com/decryptocat.php\n\n")

            f1.seek(0)

            fake_receiver_desc = {
                'gpg_key_armor': unicode(VALID_PGP_KEY1),
                'gpg_key_status': u'enabled',
                'gpg_key_fingerprint': u"CF4A22020873A76D1DCB68D32B25551568E49345",
                'username': u'fake@username.net',
                }

            # these are the same lines used in delivery_sched.py
            gpgobj = GLBGPG()
            gpgobj.load_key(VALID_PGP_KEY1)
            encrypted_file_path, encrypted_file_size = gpgobj.encrypt_file(fake_receiver_desc['gpg_key_fingerprint'],
                                                                           tempsource, f1, "/tmp")
            gpgobj.destroy_environment()

            with file(encrypted_file_path, "r") as f2:
                first_line = f2.readline()

            self.assertSubstring('-----BEGIN PGP MESSAGE-----', first_line)

            with file(encrypted_file_path, "r") as f2:
                whole = f2.read()
            self.assertEqual(encrypted_file_size, len(whole))


    @inlineCallbacks
    def test_submission_file_delivery_gpg(self):

        new_fields = MockDict().dummyFields
        new_context = MockDict().dummyContext

        new_context['steps'][0]['children'] = []

        new_context['name'] = "this uniqueness is no more checked due to the lang"
        new_context_output = yield create_context(new_context, 'en')
        self.context_assertion(new_context, new_context_output)

        doubletest = yield get_context_list('en')
        self.assertEqual(len(doubletest), 2)

        yanr = dict(MockDict().dummyReceiver)
        yanr['name'] = yanr['mail_address'] = u"quercia@nana.ptg"
        yanr['gpg_key_armor'] = unicode(VALID_PGP_KEY1)
        yanr['contexts'] = [ new_context_output['id']]
        yanr_output = yield create_receiver(yanr, 'en')
        self.receiver_assertion(yanr, yanr_output)

        asdr = dict(MockDict().dummyReceiver)
        asdr['name'] = asdr['mail_address'] = u"nocibo@rocco.tnc"
        asdr['gpg_key_armor'] = unicode(VALID_PGP_KEY1)
        asdr['contexts'] = [ new_context_output['id']]
        asdr_output = yield create_receiver(asdr, 'en')
        self.receiver_assertion(asdr, asdr_output)

        new_subm = dict(MockDict().dummySubmission)

        new_subm['finalize'] = False

        new_subm['context_id'] = new_context_output['id']
        new_subm['receivers'] = [ asdr_output['id'],
                                  yanr_output['id'] ]
        new_subm['wb_steps'] = yield fill_random_fields(new_context_output['id'])
        new_subm_output = yield create_submission(new_subm, False, 'en')
        # self.submission_assertion(new_subm, new_subm_output)

        self.emulate_file_upload(new_subm_output['id'])

        new_file = self.get_dummy_file()

        new_subm['id'] = new_subm_output['id']
        new_subm['finalize'] = True
        new_subm_output = yield update_submission(new_subm['id'], new_subm, True, 'en')

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

    def test_pgp_read_expirations(self):
        gpgobj = GLBGPG()

        self.assertEqual(gpgobj.load_key(VALID_PGP_KEY1)['expiration'],
                         datetime.utcfromtimestamp(0))

        self.assertEqual(gpgobj.load_key(EXPIRED_PGP_KEY)['expiration'],
                         datetime.utcfromtimestamp(1391012793))

        gpgobj.destroy_environment()
