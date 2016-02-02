# -*- encoding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks, returnValue

# override GLSettings
from globaleaks.orm import transact_ro
from globaleaks.settings import GLSettings
from globaleaks.jobs import delivery_sched
from globaleaks.handlers import authentication, wbtip
from globaleaks.handlers.admin.context import get_context_steps
from globaleaks.handlers.admin.receiver import create_receiver
from globaleaks.handlers.submission import create_whistleblower_tip, SubmissionInstance
from globaleaks.models import InternalTip
from globaleaks.rest import errors
from globaleaks.tests import helpers
from globaleaks.utils.token import Token

# and here, our protagonist character:
from globaleaks.handlers.submission import create_submission


class TestSubmission(helpers.TestGLWithPopulatedDB):
    compllex_field_population = True
    encryption_scenario = 'ALL_PLAINTEXT'

    @inlineCallbacks
    def create_submission(self, request):
        token = Token('submission')
        token.proof_of_work = False
        output = yield create_submission(token.id, request, True, 'en')
        returnValue(output)

    @inlineCallbacks
    def create_submission_with_files(self, request):
        token = Token('submission')
        token.proof_of_work = False
        yield self.emulate_file_upload(token, 3)
        output = yield create_submission(token.id, request, False, 'en')
        returnValue(output)

    @inlineCallbacks
    def test_create_submission_valid_submission(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        self.submission_desc = yield self.create_submission(self.submission_desc)

    @inlineCallbacks
    def test_create_submission_with_wrong_receiver(self):
        disassociated_receiver = yield create_receiver(self.get_dummy_receiver('dumb'), 'en')
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        self.submission_desc['receivers'].append(disassociated_receiver['id'])
        yield self.assertFailure(self.create_submission(self.submission_desc),
                                 errors.InvalidInputFormat)

    @inlineCallbacks
    def test_create_submission_attach_files_finalize_and_access_wbtip(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        self.submission_desc = yield self.create_submission_with_files(self.submission_desc)

        wbtip_id = yield authentication.login_whistleblower(self.submission_desc['receipt'], False)

        # remind: return a tuple (serzialized_itip, wb_itip)
        wbtip_desc = yield wbtip.get_wbtip(wbtip_id, 'en')

        self.assertTrue('answers' in wbtip_desc)

    @inlineCallbacks
    def test_create_receiverfiles_allow_unencrypted_true_no_keys_loaded(self):
        yield self.test_create_submission_attach_files_finalize_and_access_wbtip()

        yield delivery_sched.DeliverySchedule().operation()

        self.fil = yield self.get_internalfiles_by_wbtip(self.submission_desc['id'])
        self.assertTrue(isinstance(self.fil, list))
        self.assertEqual(len(self.fil), 3)

        self.rfi = yield self.get_receiverfiles_by_wbtip(self.submission_desc['id'])
        self.assertTrue(isinstance(self.rfi, list))
        self.assertEqual(len(self.rfi), 6)

        for i in range(0, 6):
            self.assertTrue(self.rfi[i]['status'] in [u'reference', u'encrypted'])

    @inlineCallbacks
    def test_submission_with_receiver_selection_allow_unencrypted_true_no_keys_loaded(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        self.submission_desc = yield self.create_submission(self.submission_desc)

    @inlineCallbacks
    def test_submission_with_receiver_selection_allow_unencrypted_false_no_keys_loaded(self):
        GLSettings.memory_copy.allow_unencrypted = False

        # Create a new request with selected three of the four receivers
        submission_request = yield self.get_dummy_submission(self.dummyContext['id'])

        yield self.assertFailure(self.create_submission(submission_request),
                                 errors.SubmissionValidationFailure)

    @inlineCallbacks
    def test_update_submission(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])

        self.submission_desc['answers'] = yield self.fill_random_answers(self.dummyContext['id'])
        self.submission_desc = yield self.create_submission(self.submission_desc)

        wbtip_id = yield authentication.login_whistleblower(self.submission_desc['receipt'], False)

        wbtip_desc = yield wbtip.get_wbtip(wbtip_id, 'en')

        self.assertTrue('answers' in wbtip_desc)


class Test_SubmissionInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = SubmissionInstance

    @inlineCallbacks
    def test_put(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        token = Token('submission')
        token.proof_of_work = False

        handler = self.request(self.submission_desc)
        yield handler.put(token.id)
