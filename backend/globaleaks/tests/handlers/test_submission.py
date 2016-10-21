# -*- encoding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks, returnValue

from globaleaks.handlers import authentication, wbtip
from globaleaks.handlers.submission import SubmissionInstance
from globaleaks.jobs import delivery_sched
from globaleaks.tests import helpers
from globaleaks.rest import errors
from globaleaks.utils.token import Token

# and here, our protagonist character:


class TestSubmissionEncryptedScenario(helpers.TestHandlerWithPopulatedDB):
    _handler = SubmissionInstance

    complex_field_population = True

    encryption_scenario = 'ENCRYPTED'

    files_created = 6

    counters_check = {
        'encrypted': 6,
        'reference': 0
    }

    @inlineCallbacks
    def create_submission(self, request):
        token = Token('submission')
        token.solve()
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        handler = self.request(self.submission_desc)
        yield handler.put(token.id)
        returnValue(self.responses[0])

    @inlineCallbacks
    def create_submission_with_files(self, request):
        token = Token('submission')
        token.solve()
        yield self.emulate_file_upload(token, 3)
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        handler = self.request(self.submission_desc)
        result = yield handler.put(token.id)
        returnValue(self.responses[0])

    @inlineCallbacks
    def test_create_submission_valid_submission(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        self.submission_desc = yield self.create_submission(self.submission_desc)

    @inlineCallbacks
    def test_create_submission_attach_files_finalize_and_verify_file_creation(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        self.submission_desc = yield self.create_submission_with_files(self.submission_desc)

        yield delivery_sched.DeliverySchedule().operation()

        self.fil = yield self.get_internalfiles_by_wbtip(self.submission_desc['id'])
        self.assertTrue(isinstance(self.fil, list))
        self.assertEqual(len(self.fil), 3)

        self.rfi = yield self.get_receiverfiles_by_wbtip(self.submission_desc['id'])
        self.assertTrue(isinstance(self.rfi, list))
        self.assertEqual(len(self.rfi), self.files_created)

        counters = {
            'encrypted': 0,
            'reference': 0
        }

        for i in range(0, self.files_created):
            if self.rfi[i]['status'] not in counters:
                counters[self.rfi[i]['status']] = 1
            else:
                counters[self.rfi[i]['status']] += 1

        for key in self.counters_check.keys():
            self.assertEqual(counters[key], self.counters_check[key])

    @inlineCallbacks
    def test_update_submission(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])

        self.submission_desc['answers'] = yield self.fill_random_answers(self.dummyContext['id'])
        self.submission_desc = yield self.create_submission(self.submission_desc)

        wbtip_id = yield authentication.login_whistleblower(self.submission_desc['receipt'], False)

        wbtip_desc = yield wbtip.get_wbtip(wbtip_id, 'en')

        self.assertTrue('answers' in wbtip_desc)

class TestSubmissionTokenInteract(helpers.TestHandlerWithPopulatedDB):
    _handler = SubmissionInstance

    @inlineCallbacks
    def test_token_must_be_solved(self):
        token = Token()
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        handler = self.request(self.submission_desc)
        yield self.assertFailure(handler.put(token.id), errors.TokenFailure)


    @inlineCallbacks
    def test_token_reuse_blocked(self):
        token = Token()
        token.solve()
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])

        handler = self.request(self.submission_desc)
        yield handler.put(token.id)
        yield self.assertFailure(handler.put(token.id), errors.TokenFailure)


class TestSubmissionEncryptedScenarioOneKeyExpired(TestSubmissionEncryptedScenario):
    encryption_scenario = 'ENCRYPTED_WITH_ONE_KEY_EXPIRED'

    files_created = 6

    counters_check = {
        'encrypted': 3,
        'unavailable': 3,
        'reference': 0
    }


class TestSubmissionEncryptedScenarioOneKeyMissing(TestSubmissionEncryptedScenario):
    encryption_scenario = 'ENCRYPTED_WITH_ONE_KEY_MISSING'

    files_created = 3

    counters_check = {
        'encrypted': 3,
        'reference': 0
    }


class TestSubmissionMixedScenario(TestSubmissionEncryptedScenario):
    encryption_scenario = 'MIXED'

    files_created = 6

    counters_check = {
        'encrypted': 3,
        'reference': 3
    }

class TestSubmissionPlaintextScenario(TestSubmissionEncryptedScenario):
    encryption_scenario = 'PLAINTEXT'

    files_created = 6

    counters_check = {
        'encrypted': 0,
        'reference': 6
    }
