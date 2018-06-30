'''Tests Submission State code'''

# -*- coding: utf-8 -*-
from globaleaks import models
from globaleaks.handlers.admin import submission_states
from globaleaks.orm import transact
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


@transact
def count_submission_states(session, tid):
    '''Counts all submission states in the system'''
    return session.query(models.SubmissionState) \
        .filter(models.SubmissionState.tid==tid).count()

@transact
def create_substate(session, submissionstate_id):
    '''Creates a test substate'''
    substate = models.SubmissionSubState()
    substate.submissionstate_id = submissionstate_id
    substate.label = {'en': "Test1"}
    substate.presentation_order = 0
    session.add(substate)


class SubmissionStateCollectionDesc(helpers.TestHandlerWithPopulatedDB):
    _handler = submission_states.SubmissionStateCollection

    def setUp(self):
        return helpers.TestHandlerWithPopulatedDB.setUp(self)

    @inlineCallbacks
    def test_get(self):
        handler = self.request({}, role='admin')
        response = yield handler.get()

        self.assertEqual(len(response), 3)

    @inlineCallbacks
    def test_post(self):
        # Create a submission state
        data_request = {
            'label': 'test_state',
            'presentation_order': 0
        }
        handler = self.request(data_request, role='admin')
        yield handler.post()

        session_state_count = yield count_submission_states(1)
        self.assertEqual(session_state_count, 4)

    @inlineCallbacks
    def test_get_with_substates(self):
        new_state_id = yield submission_states.get_id_for_system_state(1, 'new')
        yield create_substate(new_state_id)

        handler = self.request({}, role='admin')
        response = yield handler.get()

        self.assertEqual(len(response), 3)

        check_state = None
        for state in response:
            if state['id'] == new_state_id:
                check_state = state
                break

        self.assertNotEqual(check_state, None)
        self.assertEqual(len(check_state['substates']), 1)
        substate = check_state['substates'].pop()
        self.assertEqual(substate['label'], "Test1")

class SubmissionStateInstanceDesc(helpers.TestHandlerWithPopulatedDB):
    _handler = submission_states.SubmissionStateInstance

    def setUp(self):
        return helpers.TestHandlerWithPopulatedDB.setUp(self)

    def create_test_state(self):
        self._handler = submission_states.SubmissionStateCollection

        data_request = {
            'label': 'test_state',
            'presentation_order': 0
        }
        handler = self.request(data_request, role='admin')

        return handler.post()

    @inlineCallbacks
    def test_put(self):
        '''Create a new state and then edit it'''
        yield self.create_test_state()
        states = yield submission_states.retrieve_all_submission_states(1, u'en')

        for state in states:
            if state['label'] == 'test_state':
                state_uuid = state['id']

        # Change the submission state info
        data_request = {
            'label': '12345',
            'presentation_order': 0
        }

        self._handler = submission_states.SubmissionStateInstance
        handler = self.request(data_request, role='admin')
        yield handler.put(state_uuid)
        states = yield submission_states.retrieve_all_submission_states(1, u'en')

        found_label = False

        for state in states:
            if state['label'] == '12345':
                found_label = True
                break

        self.assertEqual(found_label, True)

    @inlineCallbacks
    def test_delete(self):
        '''Delete a state (if possible)'''
        yield self.create_test_state()
        states = yield submission_states.retrieve_all_submission_states(1, u'en')

        for state in states:
            if state['label'] == 'test_state':
                state_uuid = state['id']

        self._handler = submission_states.SubmissionStateInstance
        handler = self.request(role='admin')
        yield handler.delete(state_uuid)

        session_state_count = yield count_submission_states(1)
        self.assertEqual(session_state_count, 3)

    @inlineCallbacks
    def test_delete_with_substates(self):
        '''Delete a state (if possible)'''
        yield self.create_test_state()
        states = yield submission_states.retrieve_all_submission_states(1, u'en')

        for state in states:
            if state['label'] == 'test_state':
                state_uuid = state['id']
        yield create_substate(state_uuid)

        self._handler = submission_states.SubmissionStateInstance
        handler = self.request(role='admin')
        yield handler.delete(state_uuid)

        session_state_count = yield count_submission_states(1)
        self.assertEqual(session_state_count, 3)

class SubmissionSubStateCollectionDesc(helpers.TestHandlerWithPopulatedDB):
    _handler = submission_states.SubmissionSubStateCollection

    def setUp(self):
        return helpers.TestHandlerWithPopulatedDB.setUp(self)

    @inlineCallbacks
    def test_get(self):
        new_state_id = yield submission_states.get_id_for_system_state(1, 'new')
        yield create_substate(new_state_id)

        handler = self.request({}, role='admin')
        response = yield handler.get(new_state_id)
        self.assertEqual(len(response), 1)

    @inlineCallbacks
    def test_post(self):
        new_state_id = yield submission_states.get_id_for_system_state(1, 'new')
        data_request = {
            'label': '12345',
            'presentation_order': 0
        }
        handler = self.request(data_request, role='admin')
        response = yield handler.post(new_state_id)

        submission_state = yield submission_states.retrieve_specific_submission_state(1, new_state_id, u'en')
        self.assertEqual(len(submission_state['substates']), 1)

class SubmissionSubStateInstanceDesc(helpers.TestHandlerWithPopulatedDB):
    _handler = submission_states.SubmissionSubStateInstance

    def setUp(self):
        return helpers.TestHandlerWithPopulatedDB.setUp(self)

    @inlineCallbacks
    def test_put(self):
        new_state_id = yield submission_states.get_id_for_system_state(1, 'new')
        yield create_substate(new_state_id)

        submission_state = yield submission_states.retrieve_specific_submission_state(1, new_state_id, u'en')
        substate_uuid = submission_state['substates'][0]['id']

        data_request = {
            'label': '12345',
            'presentation_order': 0
        }

        handler = self.request(data_request, role='admin')
        yield handler.put(new_state_id, substate_uuid)

        submission_state = yield submission_states.retrieve_specific_submission_state(1, new_state_id, u'en')
        self.assertEqual(submission_state['substates'][0]['label'], '12345')

    @inlineCallbacks
    def test_delete(self):
        new_state_id = yield submission_states.get_id_for_system_state(1, 'new')
        yield create_substate(new_state_id)

        submission_state = yield submission_states.retrieve_specific_submission_state(1, new_state_id, u'en')
        substate_uuid = submission_state['substates'][0]['id']

        handler = self.request({}, role='admin')
        yield handler.delete(new_state_id, substate_uuid)

        submission_state = yield submission_states.retrieve_specific_submission_state(1, new_state_id, u'en')
        self.assertEqual(len(submission_state['substates']), 0)
