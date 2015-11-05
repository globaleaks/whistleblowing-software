# -*- encoding: utf-8 -*-

import os
from datetime import datetime
from twisted.internet.defer import inlineCallbacks

from globaleaks.orm import transact_ro
from globaleaks.handlers import submission
from globaleaks.handlers.admin import receiver
from globaleaks.handlers.admin.context import create_context, get_context_list
from globaleaks.jobs.delivery_sched import DeliverySchedule
from globaleaks.notification import Event
from globaleaks.rest import errors
from globaleaks.security import GLBPGP
from globaleaks.settings import GLSettings
from globaleaks.tests.helpers import MockDict, TestHandlerWithPopulatedDB, VALID_PGP_KEY1, VALID_PGP_KEY2, EXPIRED_PGP_KEY
from globaleaks.utils.token import Token
from globaleaks.utils.templating import Templating

PGPROOT = os.path.join(os.getcwd(), "testing_dir", "gnupg")


class TestPGP(TestHandlerWithPopulatedDB):
    _handler = receiver.ReceiverInstance

    def test_encrypt_message(self):
        dummy_template = "In %EventTime% you've got a crush for Taryn Southern, yay!! \
                         more info on: https://www.youtube.com/watch?v=C7JZ4F3zJdY \
                         and know that you're not alone!"

        mock_event = Event(type=u'tip',
                           trigger='Tip',
                           tip_info = {
                               'creation_date': '2013-05-13T17:49:26.105485', #epoch!
                               'id': 'useless',
                               'wb_steps' : self.fill_random_answers(self.dummyContext['id']),
                           },
                           node_info = MockDict().dummyNode,
                           receiver_info = MockDict().dummyReceiver,
                           context_info = MockDict().dummyContext,
                           subevent_info = {},
                           do_mail=False)

        mail_content = Templating().format_template(dummy_template, mock_event)

        # setup the PGP key before
        GLSettings.pgproot = PGPROOT

        fake_receiver_desc = {
            'pgp_key_public': unicode(VALID_PGP_KEY1),
            'pgp_key_fingerprint': u"CF4A22020873A76D1DCB68D32B25551568E49345",
            'pgp_key_status': u'enabled',
            'username': u'fake@username.net',
        }

        pgpobj = GLBPGP()
        pgpobj.load_key(VALID_PGP_KEY1)

        encrypted_body = pgpobj.encrypt_message(fake_receiver_desc['pgp_key_fingerprint'], mail_content)
        self.assertSubstring('-----BEGIN PGP MESSAGE-----', encrypted_body)

        pgpobj.destroy_environment()

    def test_encrypt_file(self):
        # setup the PGP key before
        GLSettings.pgproot = PGPROOT

        tempsource = os.path.join(os.getcwd(), "temp_source.txt")
        with file(tempsource, 'w+') as f1:
            f1.write("\n\nDecrypt the Cat!\n\nhttp://tobtu.com/decryptocat.php\n\n")

            f1.seek(0)

            fake_receiver_desc = {
                'pgp_key_public': unicode(VALID_PGP_KEY1),
                'pgp_key_status': u'enabled',
                'pgp_key_fingerprint': u"CF4A22020873A76D1DCB68D32B25551568E49345",
                'username': u'fake@username.net',
            }

            # these are the same lines used in delivery_sched.py
            pgpobj = GLBPGP()
            pgpobj.load_key(VALID_PGP_KEY1)
            encrypted_file_path, encrypted_file_size = pgpobj.encrypt_file(fake_receiver_desc['pgp_key_fingerprint'],
                                                                           tempsource, f1, "/tmp")
            pgpobj.destroy_environment()

            with file(encrypted_file_path, "r") as f2:
                first_line = f2.readline()

            self.assertSubstring('-----BEGIN PGP MESSAGE-----', first_line)

            with file(encrypted_file_path, "r") as f2:
                whole = f2.read()
            self.assertEqual(encrypted_file_size, len(whole))


    @inlineCallbacks
    def test_submission_file_delivery_pgp(self):
        new_fields = MockDict().dummyFields
        new_context = MockDict().dummyContext

        new_context['name'] = "this uniqueness is no more checked due to the lang"
        new_context_output = yield create_context(new_context, 'en')
        self.context_assertions(new_context, new_context_output)

        doubletest = yield get_context_list('en')
        self.assertEqual(len(doubletest), 2)

        yanr = self.get_dummy_receiver("antani1")
        yanr['pgp_key_public'] = unicode(VALID_PGP_KEY1)
        yanr['contexts'] = [ new_context_output['id']]
        yanr_output = yield receiver.create_receiver(yanr, 'en')
        self.receiver_assertions(yanr, yanr_output)

        asdr = self.get_dummy_receiver("antani2")
        asdr['pgp_key_public'] = unicode(VALID_PGP_KEY1)
        asdr['contexts'] = [ new_context_output['id']]
        asdr_output = yield receiver.create_receiver(asdr, 'en')
        self.receiver_assertions(asdr, asdr_output)

        new_subm = dict(MockDict().dummySubmission)

        new_subm['finalize'] = False

        new_subm['context_id'] = new_context_output['id']
        new_subm['receivers'] = [ asdr_output['id'],
                                  yanr_output['id'] ]
        new_subm['identity_provided'] = False
        new_subm['answers'] = yield self.fill_random_answers(new_context_output['id'])

        token = Token('submission')
        token.proof_of_work = False
        yield self.emulate_file_upload(token, 3)

        new_subm_output = yield submission.create_submission(token.id, new_subm, False, 'en')

        yield DeliverySchedule().operation()

        # now get a lots of receivertips/receiverfiles and check!
        ifilist = yield self.get_internalfiles_by_wbtip(new_subm_output['id'])

        self.assertTrue(isinstance(ifilist, list))
        self.assertEqual(len(ifilist), 3)

        rfilist = yield self.get_receiverfiles_by_wbtip(new_subm_output['id'])

        self.assertTrue(isinstance(ifilist, list))
        self.assertEqual(len(rfilist), 6)

        for i in range(0, 3):
            self.assertLess(ifilist[0]['size'], rfilist[i]['size'])

        self.assertEqual(rfilist[0]['status'], u"encrypted" )
        # completed in love! http://www.youtube.com/watch?v=CqLAwt8T3Ps

        # TODO checks the lacking of the plaintext file!, then would be completed in absolute love

    def test_pgp_read_expirations(self):
        pgpobj = GLBPGP()

        self.assertEqual(pgpobj.load_key(VALID_PGP_KEY1)['expiration'],
                         datetime.utcfromtimestamp(0))

        self.assertEqual(pgpobj.load_key(EXPIRED_PGP_KEY)['expiration'],
                         datetime.utcfromtimestamp(1391012793))

        pgpobj.destroy_environment()
