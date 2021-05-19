# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks, returnValue

from globaleaks.handlers import authentication, wbtip
from globaleaks.handlers.submission import SubmissionInstance
from globaleaks.jobs import delivery
from globaleaks.models.config import db_set_config_variable
from globaleaks.orm import tw
from globaleaks.rest import errors
from globaleaks.tests import helpers


class TestSubmissionScenario1(helpers.TestHandlerWithPopulatedDB):
    _handler = SubmissionInstance

    complex_field_population = True

    pgp_configuration = 'NONE'

    files_created = 6

    counters_check = {
        'encrypted': 0,
        'reference': 6
    }

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield tw(db_set_config_variable, 1, 'encryption', False)
        self.state.tenant_cache[1].encryption = False

    @inlineCallbacks
    def create_submission(self, request):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        handler = self.request(self.submission_desc)
        submission_id = yield handler.get()['id']
        response = yield handler.put(submission_id)
        returnValue(response['receipt'])

    @inlineCallbacks
    def create_submission_with_files(self, request):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        handler = self.request(self.submission_desc)
        submission_id = yield handler.get()['id']
        self.emulate_file_upload(submission_id, 3)
        response = yield handler.put(submission_id)
        returnValue(response['receipt'])

    @inlineCallbacks
    def test_create_submission_with_no_recipients(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        self.submission_desc['receivers'] = []
        handler = self.request(self.submission_desc)
        submission_id = yield handler.get()['id']
        self.assertFailure(handler.put(submission_id), errors.InputValidationError)

    @inlineCallbacks
    def test_create_simple_submission(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        yield self.create_submission(self.submission_desc)

    @inlineCallbacks
    def test_create_submission_attach_files_finalize_and_verify_file_creation(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        receipt = yield self.create_submission_with_files(self.submission_desc)

        yield delivery.Delivery().run()

        self.fil = yield self.get_internalfiles_by_receipt(receipt)
        self.assertTrue(isinstance(self.fil, list))
        self.assertEqual(len(self.fil), 3)

        self.rfi = yield self.get_receiverfiles_by_receipt(receipt)
        self.assertTrue(isinstance(self.rfi, list))
        self.assertEqual(len(self.rfi), self.files_created)

        counters = {
            'encrypted': 0,
            'reference': 0
        }

        for i in range(self.files_created):
            if self.rfi[i]['status'] not in counters:
                counters[self.rfi[i]['status']] = 1
            else:
                counters[self.rfi[i]['status']] += 1

        for key in self.counters_check:
            self.assertEqual(counters[key], self.counters_check[key])

    @inlineCallbacks
    def test_update_submission(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])

        self.submission_desc['answers'] = yield self.fill_random_answers(self.dummyContext['questionnaire_id'])
        receipt = yield self.create_submission(self.submission_desc)

        session = yield authentication.login_whistleblower(1, receipt)

        wbtip_desc, _ = yield wbtip.get_wbtip(session.user_id, 'en')

        self.assertTrue('data' in wbtip_desc)


class TestSubmission(helpers.TestHandlerWithPopulatedDB):
    _handler = SubmissionInstance

    @inlineCallbacks
    def test_token_reuse_blocked(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])

        handler = self.request(self.submission_desc)

        self.assertFalse(handler.token.id in self.state.tokens)

        submission_id = yield handler.get()['id']

        self.assertFalse(handler.token.id in self.state.tokens)


class TestSubmissionScenario2(TestSubmissionScenario1):
    pgp_configuration = 'ONE_VALID_ONE_EXPIRED'

    counters_check = {
        'encrypted': 6,
        'reference': 0
    }


class TestSubmissionScenario3(TestSubmissionScenario1):
    pgp_configuration = 'ONE_VALID_ONE_WITHOUT'

    counters_check = {
        'encrypted': 3,
        'reference': 3
    }


class TestSubmissionScenario4(TestSubmissionScenario1):
    pgp_configuration = 'ALL'

    counters_check = {
        'encrypted': 6,
        'reference': 0
    }
