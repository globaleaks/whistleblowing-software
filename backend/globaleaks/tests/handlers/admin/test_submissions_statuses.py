# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.admin import submission_statuses
from globaleaks.orm import transact
from globaleaks.tests import helpers


@transact
def count_submission_statuses(session, tid):
    """Counts all submission statuses in the system"""
    return session.query(models.SubmissionStatus) \
        .filter(models.SubmissionStatus.tid==tid).count()


@transact
def create_substatus(session, submissionstatus_id):
    """Creates a test substatus"""
    substatus = models.SubmissionSubStatus()
    substatus.submissionstatus_id = submissionstatus_id
    substatus.label = {'en': "Test1"}
    substatus.presentation_order = 0
    session.add(substatus)


class SubmissionStatusCollectionDesc(helpers.TestHandlerWithPopulatedDB):
    _handler = submission_statuses.SubmissionStatusCollection

    def setUp(self):
        return helpers.TestHandlerWithPopulatedDB.setUp(self)

    @inlineCallbacks
    def test_get(self):
        handler = self.request({}, role='admin')
        response = yield handler.get()

        self.assertEqual(len(response), 3)

    @inlineCallbacks
    def test_post(self):
        # Create a submission status
        data_request = {
            'label': 'test_status',
            'presentation_order': 0
        }

        handler = self.request(data_request, role='admin')
        yield handler.post()

        session_status_count = yield count_submission_statuses(1)
        self.assertEqual(session_status_count, 4)

    @inlineCallbacks
    def test_get_with_substatuses(self):
        new_status_id = yield submission_statuses.get_id_for_system_status(1, 'new')
        yield create_substatus(new_status_id)

        handler = self.request({}, role='admin')
        response = yield handler.get()

        self.assertEqual(len(response), 3)

        check_status = None
        for status in response:
            if status['id'] == new_status_id:
                check_status = status
                break

        self.assertNotEqual(check_status, None)
        self.assertEqual(len(check_status['substatuses']), 1)
        substatus = check_status['substatuses'].pop()
        self.assertEqual(substatus['label'], "Test1")

class SubmissionStatusInstanceDesc(helpers.TestHandlerWithPopulatedDB):
    _handler = submission_statuses.SubmissionStatusInstance

    def setUp(self):
        return helpers.TestHandlerWithPopulatedDB.setUp(self)

    def create_test_status(self):
        self._handler = submission_statuses.SubmissionStatusCollection

        data_request = {
            'label': 'test_status',
            'presentation_order': 0
        }
        handler = self.request(data_request, role='admin')

        return handler.post()

    @inlineCallbacks
    def test_put(self):
        """Create a new status and then edit it"""
        yield self.create_test_status()
        statuses = yield submission_statuses.retrieve_all_submission_statuses(1, u'en')

        for status in statuses:
            if status['label'] == 'test_status':
                status_uuid = status['id']

        # Change the submission status info
        data_request = {
            'label': '12345',
            'presentation_order': 0
        }

        self._handler = submission_statuses.SubmissionStatusInstance
        handler = self.request(data_request, role='admin')
        yield handler.put(status_uuid)
        statuses = yield submission_statuses.retrieve_all_submission_statuses(1, u'en')

        found_label = False

        for status in statuses:
            if status['label'] == '12345':
                found_label = True
                break

        self.assertEqual(found_label, True)

    @inlineCallbacks
    def test_delete(self):
        """Delete a status (if possible)"""
        yield self.create_test_status()
        statuses = yield submission_statuses.retrieve_all_submission_statuses(1, u'en')

        for status in statuses:
            if status['label'] == 'test_status':
                status_uuid = status['id']

        self._handler = submission_statuses.SubmissionStatusInstance
        handler = self.request(role='admin')
        yield handler.delete(status_uuid)

        session_status_count = yield count_submission_statuses(1)
        self.assertEqual(session_status_count, 3)

    @inlineCallbacks
    def test_delete_with_substatuses(self):
        """Delete a status (if possible)"""
        yield self.create_test_status()
        statuses = yield submission_statuses.retrieve_all_submission_statuses(1, u'en')

        for status in statuses:
            if status['label'] == 'test_status':
                status_uuid = status['id']
        yield create_substatus(status_uuid)

        self._handler = submission_statuses.SubmissionStatusInstance
        handler = self.request(role='admin')
        yield handler.delete(status_uuid)

        session_status_count = yield count_submission_statuses(1)
        self.assertEqual(session_status_count, 3)


class SubmissionSubStatusCollectionDesc(helpers.TestHandlerWithPopulatedDB):
    _handler = submission_statuses.SubmissionSubStatusCollection

    def setUp(self):
        return helpers.TestHandlerWithPopulatedDB.setUp(self)

    @inlineCallbacks
    def test_get(self):
        new_status_id = yield submission_statuses.get_id_for_system_status(1, 'new')
        yield create_substatus(new_status_id)

        handler = self.request({}, role='admin')
        response = yield handler.get(new_status_id)
        self.assertEqual(len(response), 1)

    @inlineCallbacks
    def test_post(self):
        new_status_id = yield submission_statuses.get_id_for_system_status(1, 'new')
        data_request = {
            'label': '12345',
            'presentation_order': 0
        }
        handler = self.request(data_request, role='admin')
        response = yield handler.post(new_status_id)

        submission_status = yield submission_statuses.retrieve_specific_submission_status(1, new_status_id, u'en')
        self.assertEqual(len(submission_status['substatuses']), 1)

class SubmissionSubStatusInstanceDesc(helpers.TestHandlerWithPopulatedDB):
    _handler = submission_statuses.SubmissionSubStatusInstance

    def setUp(self):
        return helpers.TestHandlerWithPopulatedDB.setUp(self)

    @inlineCallbacks
    def test_put(self):
        new_status_id = yield submission_statuses.get_id_for_system_status(1, 'new')
        yield create_substatus(new_status_id)

        submission_status = yield submission_statuses.retrieve_specific_submission_status(1, new_status_id, u'en')
        substatus_uuid = submission_status['substatuses'][0]['id']

        data_request = {
            'label': '12345',
            'presentation_order': 0
        }

        handler = self.request(data_request, role='admin')
        yield handler.put(new_status_id, substatus_uuid)

        submission_status = yield submission_statuses.retrieve_specific_submission_status(1, new_status_id, u'en')
        self.assertEqual(submission_status['substatuses'][0]['label'], '12345')

    @inlineCallbacks
    def test_delete(self):
        new_status_id = yield submission_statuses.get_id_for_system_status(1, 'new')
        yield create_substatus(new_status_id)

        submission_status = yield submission_statuses.retrieve_specific_submission_status(1, new_status_id, u'en')
        substatus_uuid = submission_status['substatuses'][0]['id']

        handler = self.request({}, role='admin')
        yield handler.delete(new_status_id, substatus_uuid)

        submission_status = yield submission_statuses.retrieve_specific_submission_status(1, new_status_id, u'en')
        self.assertEqual(len(submission_status['substatuses']), 0)
