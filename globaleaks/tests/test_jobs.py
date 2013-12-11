from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers
from globaleaks.jobs import delivery_sched

from globaleaks.handlers.receiver import get_receiver_tip_list
from globaleaks.handlers.submission import create_submission
from globaleaks.handlers.node import get_public_context_list, get_public_receiver_list

class TestJobs(helpers.TestGL):

    @inlineCallbacks
    def test_tip_creation(self):

        receivers = yield get_public_receiver_list('en')
        contexts = yield get_public_context_list('en')

        yield create_submission(self.dummySubmission, finalize=True)
        created_tips = yield delivery_sched.tip_creation()
        self.assertEqual(len(created_tips), 2) # this createSubmission and the helpers one

        receiver_tips = yield get_receiver_tip_list(self.dummyReceiver['receiver_gus'])

        expected_keys = ['access_counter',
                         'creation_date',
                         'expiration_date',
                         'last_access',
                         'expressed_pertinence',
                         'id',
                         'comments_number',
                         'files_number',
                         'context_name',
                         'preview', 'read_messages',
                         'unread_messages',
                         'your_messages']

        self.assertEqual(set(receiver_tips[0].keys()), set(expected_keys))
