import json

from twisted.internet.defer import inlineCallbacks

from globaleaks.jobs import delivery_sched
from globaleaks.handlers import files, authentication, submission, tip
from globaleaks.tests import helpers
from globaleaks.handlers.admin import update_context, create_receiver, get_receiver_list, get_context_list

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
    def test_create_submission(self):
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
    def test_create_internalfiles(self):
        yield self.create_dummy_files()
        # fill self.file_list
        for file_desc in self.file_list:
            keydiff = set(['size', 'content_type', 'name', 'creation_date', 'id']) - set(file_desc.keys())
            self.assertFalse(keydiff)

    @inlineCallbacks
    def test_access_from_receipt(self):
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
    def test_submission_with_files(self):
        yield self.create_dummy_files()

        submission_desc = self.dummySubmission
        submission_desc['finalize'] = True
        del submission_desc['submission_gus']
        status = yield submission.create_submission(submission_desc, finalize=True)
        receipt = yield submission.create_whistleblower_tip(status)

        wb_tip_id = yield authentication.login_wb(receipt)
        wb_tip = yield tip.get_internaltip_wb(wb_tip_id)

        receiver_tips = yield delivery_sched.tip_creation()

        self.assertEqual(len(receiver_tips), 1)
        
        filesdict = yield delivery_sched.file_preprocess()
        processdict = delivery_sched.file_process(filesdict)

        self.assertEqual(len(processdict), 2)
        
        receiverfile_list = yield delivery_sched.receiver_file_align(filesdict, processdict)

        receiver_files = []
        for file_id in receiverfile_list:
            tip_id = receiver_tips[0]
            receiver_file = yield files.get_receiver_file(tip_id, file_id)
            receiver_files.append(receiver_file)
        self.assertEqual(len(receiver_files), 2)

    # --------------------------------------------------------- #
    def get_new_receiver_desc(self, descpattern):
        new_r = dict(self.dummyReceiver)
        new_r['name'] = new_r['description'] = new_r['username'] =\
        new_r['notification_fields']['mail_address'] = unicode("%s@%s.xxx" % (descpattern, descpattern))
        return new_r

    @inlineCallbacks
    def test_submission_with_receiver_selection(self):

        yield create_receiver(self.get_new_receiver_desc("second"))
        yield create_receiver(self.get_new_receiver_desc("third"))
        yield create_receiver(self.get_new_receiver_desc("fourth"))

        # for some reason, the first receiver is no more with the same ID
        self.receivers = yield get_receiver_list()
        print len(self.receivers)

        self.dummyContext['receivers'] = [ self.receivers[0]['receiver_gus'],
                                           self.receivers[1]['receiver_gus'],
                                           self.receivers[2]['receiver_gus'],
                                           self.receivers[3]['receiver_gus'] ]

        self.dummyContext['selectable_receiver'] = True
        self.dummyContext['escalation_threshold'] = 0

        context_status = yield update_context(self.dummyContext['context_gus'], self.dummyContext)

        # Create a new request with selected three of the four receivers
        submission_request= self.dummySubmission
        submission_request['context_gus'] = context_status['context_gus']
        submission_request['submission_gus'] = ''
        submission_request['finalize'] = True
        submission_request['receivers'] = [ self.receivers[0]['receiver_gus'],
                                            self.receivers[1]['receiver_gus'],
                                            self.receivers[2]['receiver_gus'] ]

        print submission_request
        status = yield submission.create_submission(submission_request, finalize=True)
        print "XX", status
        receiver_tips = yield delivery_sched.tip_creation()
        print "YY", receiver_tips
        self.assertEqual(len(receiver_tips), 3)

    @inlineCallbacks
    def test_update_submission(self):
        submission_desc = self.dummySubmission
        submission_desc['finalize'] = False
        submission_desc['context_gus'] = self.dummyContext['context_gus']

        status = yield submission.create_submission(submission_desc, finalize=False)

        status['wb_fields'] = { 'city': "NY", 'Sun': "Flashy",
                                'dict2': "ottimo direi", 'dict3': "bingo bongo"}

        status['finalize'] = True

        status = yield submission.update_submission(status['submission_gus'], status, finalize=True)
        receipt = yield submission.create_whistleblower_tip(status)

        wb_access_id = yield authentication.login_wb(receipt)

        # remind: return a tuple (serzialized_itip,wb_tip_id)
        (wb_tip, wb_tip_id) = yield tip.get_internaltip_wb(wb_access_id)
        self.assertTrue(wb_tip['fields']['dict2'] == status['wb_fields']['dict2'])


    #@inlineCallbacks
    #def test_unable_to_access_submission(self):
