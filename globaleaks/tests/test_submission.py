import unittest

from twisted.internet.defer import inlineCallbacks

from globaleaks.jobs import delivery_sched
from globaleaks.handlers import files, authentication, submission, tip
from globaleaks.tests import helpers
from globaleaks.handlers.admin import update_context, create_receiver, get_receiver_list

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

    @inlineCallbacks
    def create_dummy_files(self):
        relationship = files.dump_files_fs(self.dummyFiles)
        file_list = yield files.register_files_db(self.dummyFiles,
                relationship, self.dummySubmission['submission_gus'])

        for file_desc in file_list:
            self.assertTrue(set(['size', 'content_type', 'name', 'creation_date', 'id']) == set(file_desc.keys()))

    @inlineCallbacks
    def test_submission_with_files(self):
        status = yield submission.update_submission(self.dummySubmission['submission_gus'], self.dummySubmission)
        
        yield self.create_dummy_files()

        receipt = yield submission.create_whistleblower_tip(status)
        yield submission.finalize_submission(status['id'])

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

    @inlineCallbacks
    def test_update_submission(self):
        status = yield submission.update_submission(self.dummySubmission['submission_gus'], self.dummySubmission)

        receipt = yield submission.create_whistleblower_tip(status)
        yield submission.finalize_submission(status['id'])

        import re
        retval = re.match('(\w+){10}', receipt)
        self.assertTrue(retval)

    @inlineCallbacks
    def test_create_submission(self):
        status = yield submission.create_submission(self.dummySubmission)

        receipt = yield submission.create_whistleblower_tip(status)
        yield submission.finalize_submission(status['id'])

        import re
        retval = re.match('(\w+){10}', receipt)
        self.assertTrue(retval)

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

        self.dummyContext['receivers'] = [ self.receivers[0]['receiver_gus'],
                                           self.receivers[1]['receiver_gus'],
                                           self.receivers[2]['receiver_gus'],
                                           self.receivers[3]['receiver_gus'] ]

        self.dummyContext['selectable_receiver'] = True
        self.dummyContext['escalation_threshold'] = 0

        context_status = yield update_context(self.dummyContext['context_gus'], self.dummyContext)

        # Create a new request with selected three of the four receivers
        submission_request= dict(self.dummySubmission)
        submission_request['context_gus'] = context_status['context_gus']
        submission_request['submission_gus'] = ''
        submission_request['finalize'] = True
        submission_request['receivers'] = [ self.receivers[0]['receiver_gus'],
                                            self.receivers[1]['receiver_gus'],
                                            self.receivers[2]['receiver_gus'] ]

        status = yield submission.update_submission(self.dummySubmission['submission_gus'], submission_request)
        yield submission.finalize_submission(status['id'])

        receiver_tips = yield delivery_sched.tip_creation()
        self.assertEqual(len(receiver_tips), 3)
