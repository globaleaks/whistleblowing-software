import json

from twisted.internet.defer import inlineCallbacks
from globaleaks import models

from globaleaks.jobs import delivery_sched
from globaleaks.handlers import files, authentication, submission, tip
from globaleaks.jobs.delivery_sched import APSDelivery
from globaleaks.jobs.notification_sched import APSNotification
from globaleaks.tests import helpers
from globaleaks.handlers.admin import update_context, create_receiver, get_receiver_list
from globaleaks.rest import errors
from globaleaks.settings import transact
from globaleaks.models import ReceiverTip


class TestSubmission(helpers.TestGL):
    dummyFiles = [{'body': 'spam',
            'content_type': 'application/octet',
            'filename': 'spam'},
            {'body': 'ham', 
            'content_type': 'application/octet',
            'filename': 'ham'}
    ]
    
    @inlineCallbacks
    def setUp(self):
        self.setUp_dummy()
        yield self.initalize_db()


    # --------------------------------------------------------- #
    @inlineCallbacks
    def test_1_create_submission(self):
        submission_desc = self.dummySubmission
        submission_desc['finalize'] = True
        del submission_desc['submission_gus']

        status = yield submission.create_submission(submission_desc, finalize=True)
        receipt = yield submission.create_whistleblower_tip(status)

        import re
        retval = re.match('(\w+){10}', receipt)
        self.assertTrue(retval)

    @inlineCallbacks
    def create_dummy_files(self):
        relationship = files.dump_files_fs(self.dummyFiles)
        self.file_list = yield files.register_files_db(self.dummyFiles,
                relationship, self.dummySubmission['submission_gus'])

    @inlineCallbacks
    def test_2_create_internalfiles(self):
        yield self.create_dummy_files()
        # fill self.file_list
        for file_desc in self.file_list:
            keydiff = set(['size', 'content_type', 'name', 'creation_date', 'id']) - set(file_desc.keys())
            self.assertFalse(keydiff)

    @inlineCallbacks
    def test_3_access_from_receipt(self):
        submission_desc = self.dummySubmission
        submission_desc['finalize'] = True
        del submission_desc['submission_gus']

        status = yield submission.create_submission(submission_desc, finalize=True)
        receipt = yield submission.create_whistleblower_tip(status)

        wb_access_id = yield authentication.login_wb(receipt)

        # remind: return a tuple (serzialized_itip,
        (wb_tip, wb_tip_id) = yield tip.get_internaltip_wb(wb_access_id)

        # In the WB/Receiver Tip interface, wb_fields are called fields.
        # This can be uniformed when API would be cleaned of the _gus
        self.assertTrue(wb_tip_id == wb_access_id)
        self.assertTrue(wb_tip.has_key('fields'))
        self.assertTrue(wb_tip['fields'].has_key('Sun'))


    @inlineCallbacks
    def test_4_submission_with_files(self):
        yield self.create_dummy_files()

        submission_desc = self.dummySubmission
        submission_desc['finalize'] = False
        del submission_desc['submission_gus']
        submission_desc['receivers'] = [ self.dummyReceiver['receiver_gus'] ]

        status = yield submission.create_submission(submission_desc, finalize=False)

        # --- Emulate file upload before assign them to the submission
        filesdict = yield delivery_sched.file_preprocess()
        self.assertEqual(len(filesdict), 2)

        processdict = delivery_sched.file_process(filesdict)
        # Checks the SHA2SUM computed
        for random_f_id, sha2sum in processdict.iteritems():
            if sha2sum == "0eccfe263668d171bd19b7d491c3ef5c43559e6d3acf697ef37596181c6fdf4c":
                continue
            if sha2sum == "4e388ab32b10dc8dbc7e28144f552830adc74787c1e2c0824032078a79f227fb":
                continue
            self.assertTrue(False) # Checksum expected unable to be computed

        receiverfile_list = yield delivery_sched.receiver_file_align(filesdict, processdict)

        # --- Complete submission
        internalfiles_id_list = []
        for itip_id in filesdict.iterkeys():
            internalfiles_id_list.append(itip_id)

        status['files'] = internalfiles_id_list
        status['finalize'] = True
        status = yield submission.create_submission(status, finalize=True)

        self.assertEqual(len(status['files']), 2)

        new_rtip = yield delivery_sched.tip_creation()

        self.assertEqual(len(processdict), 2)
        self.assertEqual(len(receiverfile_list), 2)

        receiver_files = []
        for file_id in receiverfile_list:
            tip_id = new_rtip[0]
            receiver_file = yield files.get_receiver_file(tip_id, file_id)
            receiver_files.append(receiver_file)

        self.assertEqual(len(receiver_files), 2)


    def get_new_receiver_desc(self, descpattern):
        new_r = dict(self.dummyReceiver)
        new_r['name'] = new_r['description'] = new_r['username'] =\
        new_r['notification_fields']['mail_address'] = unicode("%s@%s.xxx" % (descpattern, descpattern))
        return new_r

    @inlineCallbacks
    def test_5_submission_with_receiver_selection(self):

        yield create_receiver(self.get_new_receiver_desc("second"))
        yield create_receiver(self.get_new_receiver_desc("third"))
        yield create_receiver(self.get_new_receiver_desc("fourth"))

        # for some reason, the first receiver is no more with the same ID
        self.receivers = yield get_receiver_list()

        self.assertEqual(len(self.receivers), 4)

        self.dummyContext['receivers'] = [ self.receivers[0]['receiver_gus'],
                                           self.receivers[1]['receiver_gus'],
                                           self.receivers[2]['receiver_gus'],
                                           self.receivers[3]['receiver_gus'] ]
        self.dummyContext['selectable_receiver'] = True
        self.dummyContext['escalation_threshold'] = 0

        context_status = yield update_context(self.dummyContext['context_gus'], self.dummyContext)

        # Create a new request with selected three of the four receivers
        submission_request= self.dummySubmission
        # submission_request['context_gus'] = context_status['context_gus']
        submission_request['submission_gus'] = submission_request['id'] = ''
        submission_request['finalize'] = False
        submission_request['receivers'] = [ self.receivers[0]['receiver_gus'],
                                            self.receivers[1]['receiver_gus'],
                                            self.receivers[2]['receiver_gus'] ]

        status = yield submission.create_submission(submission_request, finalize=False)
        just_empty_eventually_internaltip = yield delivery_sched.tip_creation()

        # Checks, the submission need to be the same now
        self.assertEqual(len(submission_request['receivers']), len(status['receivers']))

        status['finalize'] = True
        submission_request['context_gus'] = context_status['context_gus'] # reused
        status['receivers'] = [ self.receivers[0]['receiver_gus'],
                                self.receivers[3]['receiver_gus'] ]

        status = yield submission.update_submission(status['submission_gus'], status, finalize=True)

        receiver_tips = yield delivery_sched.tip_creation()
        self.assertEqual(len(receiver_tips), len(status['receivers']))


    @inlineCallbacks
    def test_6_update_submission(self):
        submission_desc = self.dummySubmission
        submission_desc['finalize'] = False
        submission_desc['context_gus'] = self.dummyContext['context_gus']
        submission_desc['submission_gus'] = submission_desc['id'] = submission_desc['mark'] = None

        status = yield submission.create_submission(submission_desc, finalize=False)

        status['wb_fields'] = { 'city': u"NY", 'Sun': u"Flashy",
                                'dict2': u"ottimo direi", 'dict3': u"bingo bongo"}

        status['finalize'] = True

        status = yield submission.update_submission(status['submission_gus'], status, finalize=True)

        receipt = yield submission.create_whistleblower_tip(status)
        wb_access_id = yield authentication.login_wb(receipt)

        # remind: return a tuple (serzialized_itip,wb_tip_id)
        (wb_tip, wb_tip_id) = yield tip.get_internaltip_wb(wb_access_id)
        self.assertTrue(wb_tip['fields']['dict2'] == status['wb_fields']['dict2'])


    @inlineCallbacks
    def test_7_unable_to_access_finalized(self):
        submission_desc = self.dummySubmission
        submission_desc['finalize'] = True
        submission_desc['context_gus'] = self.dummyContext['context_gus']

        status = yield submission.create_submission(submission_desc, finalize=True)
        try:
            yield submission.update_submission(status['submission_gus'], status, finalize=True)
        except errors.SubmissionConcluded:
            self.assertTrue(True)
            return
        self.assertTrue(False)

        # self.assertRaises(errors.SubmissionConcluded,
        #   (yield submission.update_submission(status['submission_gus'], status, finalize=True)) )


    @transact
    def systemsetting_setup(self, store):
        node = store.find(models.Node).one()
        node.notification_settings["server"] = "box549.bluehost.com"
        node.notification_settings["port"] = 25
        node.notification_settings["username"] ="sendaccount939@globaleaks.org"
        # node.notification_settings["password"] ="sendaccount939"
        node.notification_settings["password"] ="wrong"
        # XXX - I don't want a mail every check
        node.notification_settings["ssl"] = False

    @inlineCallbacks
    def test_8_sendmail_wrongconf(self):
        # Currently disabled, checks password few line over here
        self.dummyReceiver['notification_fields']['mail_address'] = 'vecna@globaleaks.org'
        self.dummyReceiver['receiver_level'] = 1
        yield self.systemsetting_setup()

        delivery_sched.tip_creation()
        APSNotification().operation()
