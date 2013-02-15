#import sys

from twisted.python import log
from twisted.internet.defer import inlineCallbacks
from twisted.trial import unittest

from globaleaks.jobs import delivery_sched
from globaleaks.handlers import files, authentication, submission, tip
from globaleaks.tests import helpers

#log.startLogging(sys.stdout)
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
    def dtest_new_submission(self):
        status = yield submission.create_submission(self.dummySubmission)
        print status
    
    @inlineCallbacks
    def test_new_submission_with_files(self):
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
        
        receiver_files = yield tip.get_files_receiver(status['receivers'][0], receiver_tips[0])
        self.assertEqual(len(receiver_files), 2)

# 
#         for file_id in receiverfile_list:
#             tip_id = receiver_tips[0]
#             receiver_file = yield files.download_file(tip_id, file_id)
#             receiver_files.append(receiver_file)




