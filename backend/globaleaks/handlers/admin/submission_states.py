# Handle manipulation of submission states
import base64
import os
import uuid

from six import text_type

from twisted.internet import threads
from twisted.internet.defer import inlineCallbacks, returnValue

from globaleaks import models
from globaleaks.rest import errors
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.operation import OperationHandler
from globaleaks.orm import transact
from globaleaks.rest import requests
from globaleaks.utils.security import directory_traversal_check
from globaleaks.utils.utility import uuid4


def serialize_submission_state(session, row):
    submission_state = {
        'id': row.id,
        'tid': row.tid,
        'label': row.label,
        'system_defined': row.system_defined,
        'system_usage': row.system_usage,
        'presentation_order': row.presentation_order,
        'substates': []
    }

    # See if we have any substates we need to serialize
    substate_rows = session.query(models.SubmissionSubStates) \
        .filter(models.SubmissionSubStates.submissionstate_id == row.id) \
        .order_by(models.SubmissionSubStates.presentation_order)

    for substate_row in substate_rows:
        submission_state['substates'].append(
            serialized_submission_substate(substate_row)
        )

    return submission_state


def serialized_submission_substate(row):
    '''Serializes the submission's substates'''
    submission_substate = {
        'id': row.id,
        'label': row.label,
        'submissionstate_id': row.submissionstate_id,
        'presentation_order': row.presentation_order
    }

    return submission_substate


@transact
def retrieve_all_submission_states(session, tid):
    return db_retrieve_all_submission_states(session, tid)


def db_retrieve_all_submission_states(session, tid):
    '''Retrieves all submission states'''
    submission_states = []
    user_submission_states = []

    rows = session.query(models.SubmissionStates) \
        .filter(models.SubmissionStates.tid == tid) \
        .order_by(models.SubmissionStates.presentation_order)

    # We need special handle system states vs. user defined ones
    new_state = None
    open_state = None
    closed_state = None

    for row in rows:
        if row.system_defined is False:
            user_submission_states.append(
                serialize_submission_state(session, row)
            )
        elif row.system_usage == 'new':
            new_state = serialize_submission_state(session, row)
        elif row.system_usage == 'open':
            open_state = serialize_submission_state(session, row)
        elif row.system_usage == 'closed':
            closed_state = serialize_submission_state(session, row)

    # Build the final array in the correct order
    submission_states.append(new_state)
    submission_states.append(open_state)
    submission_states += user_submission_states
    submission_states.append(closed_state)

    # Now we need to return it in the properly sorted order
    return submission_states


@transact
def retrieve_specific_submission_state(session, tid, submission_state_uuid):
    return db_retrieve_specific_submission_state(session, tid, submission_state_uuid)


def db_retrieve_specific_submission_state(session, tid, submission_state_uuid):
    state = session.query(models.SubmissionStates) \
        .filter(models.SubmissionStates.tid == tid, \
                models.SubmissionStates.id == submission_state_uuid).first()

    if state is None:
        raise errors.ResourceNotFound

    return serialize_submission_state(session, state)


def update_state_model_from_request(model_obj, request):
    '''Populates the model from the request, as well as setting default values'''
    model_obj.label = request['label']
    model_obj.presentation_order = request['presentation_order']
    return model_obj


@transact
def create_submission_state(session, tid, request):
    '''Creates submission state'''
    new_state = models.SubmissionStates()
    new_state.id = text_type(uuid.uuid4())
    new_state.tid = tid

    update_state_model_from_request(new_state, request)

    session.add(new_state)
    session.commit()


@transact
def update_submission_state(session, tid, submission_state_uuid, request):
    state = session.query(models.SubmissionStates) \
        .filter(models.SubmissionStates.tid == tid, \
                models.SubmissionStates.id == submission_state_uuid).first()

    if state is None:
        raise errors.ResourceNotFound

    state = update_state_model_from_request(state, request)
    session.merge(state)
    session.commit()


@transact
def get_id_for_system_state(session, tid, system_state):
    return db_get_id_for_system_state(session, tid, system_state)


def db_get_id_for_system_state(session, tid, system_state):
    '''Returns the UUID of a given submission state'''
    state = session.query(models.SubmissionStates) \
        .filter(models.SubmissionStates.tid == tid, \
                models.SubmissionStates.system_usage == system_state).first()

    if state is None:
        raise errors.ResourceNotFound

    return state.id


@transact
def get_submission_state(session, tid, submission_state_uuid):
    '''Returns the UUID of a given submission state'''
    state = session.query(models.SubmissionStates) \
        .filter(models.SubmissionStates.tid == tid, \
                models.SubmissionStates.id == submission_state_uuid).first()

    if state is None:
        raise errors.ResourceNotFound

    return state


def update_substate_model_from_request(model_obj, substate_request):
    '''Populates the model off each value from requests['substate']'''
    model_obj.label = substate_request['label']
    model_obj.presentation_order = substate_request['presentation_order']
    return model_obj


@transact
def update_submission_substate(session, tid, submission_state_uuid, substate_uuid, request):
    # Safety check
    db_retrieve_specific_submission_state(session, tid, submission_state_uuid)

    substate = session.query(models.SubmissionSubStates) \
        .filter(models.SubmissionSubStates.submissionstate_id == submission_state_uuid, \
                models.SubmissionSubStates.id == substate_uuid).first()

    if substate is None:
        raise errors.ResourceNotFound

    substate = update_substate_model_from_request(substate, request)
    session.merge(substate)
    session.commit()


@transact
def create_submission_substate(session, tid, submission_state_uuid, request):
    '''Creates a substate'''

    # Safety check here, make sure that the submission state we're looking for
    # 1. exists
    # 2. is part of our tid
    db_retrieve_specific_submission_state(session, tid, submission_state_uuid)

    substate_obj = models.SubmissionSubStates()
    substate_obj.submissionstate_id = submission_state_uuid

     # submissionsate_id is not normally set from requests; unsafe to do so because
     # as it should never change in normal operations
    substate_obj.submissionstate_id = submission_state_uuid

    update_substate_model_from_request(substate_obj, request)
    session.add(substate_obj)

@transact
def order_state_elements(session, handler, req_args, *args, **kwargs):
    states = session.query(models.SubmissionStates).filter(
        models.SubmissionStates.tid == handler.request.tid,
        models.SubmissionStates.system_defined == 0)

    id_dict = {state.id: state for state in states}
    ids = req_args['ids']

    if len(ids) != len(id_dict) or set(ids) != set(id_dict):
        raise errors.InputValidationError('list does not contain all context ids')

    for i, state_id in enumerate(ids):
        id_dict[state_id].presentation_order = i

@transact
def order_substate_elements(session, handler, req_args, *args, **kwargs):
    submission_state_id = args[0]

    substates = session.query(models.SubmissionSubStates).filter(
        models.SubmissionSubStates.submissionstate_id == submission_state_id)

    id_dict = {substate.id: substate for substate in substates}
    ids = req_args['ids']

    if len(ids) != len(id_dict) or set(ids) != set(id_dict):
        raise errors.InputValidationError('list does not contain all context ids')

    for i, substate_id in enumerate(ids):
        id_dict[substate_id].presentation_order = i

class SubmissionStateCollection(OperationHandler):
    '''Handles submission states on the backend'''
    check_roles = 'admin'

    def get(self):
        return retrieve_all_submission_states(self.request.tid)

    def post(self):
        request = self.validate_message(self.request.content.read(),
                                        requests.SubmissionStateDesc)

        return create_submission_state(self.request.tid, request)

    def operation_descriptors(self):
        return {
            'order_elements': (order_state_elements, {'ids': [text_type]}),
        }

class SubmissionStateInstance(BaseHandler):
    '''Manipulates a specific submission state'''
    check_roles = 'admin'

    def put(self, submission_state_uuid):
        request = self.validate_message(self.request.content.read(),
                                        requests.SubmissionStateDesc)

        return update_submission_state(self.request.tid, submission_state_uuid, request)

    def delete(self, submission_state_uuid):
        return models.delete(models.SubmissionStates, \
                             models.SubmissionStates.tid == self.request.tid, \
                             models.SubmissionStates.id == submission_state_uuid)

class SubmissionSubStateCollection(OperationHandler):
    '''Manages substates for a given state'''
    check_roles = 'admin'

    @inlineCallbacks
    def get(self, submission_state_uuid):
        submission_state = yield retrieve_specific_submission_state(self.request.tid, submission_state_uuid)

        returnValue(submission_state['substates'])

    def post(self, submission_state_uuid):
        request = self.validate_message(self.request.content.read(),
                                        requests.SubmissionSubStateDesc)

        return create_submission_substate(self.request.tid, submission_state_uuid, request)

    def operation_descriptors(self):
        return {
            'order_elements': (order_substate_elements, {'ids': [text_type]}),
        }

class SubmissionSubStateInstance(BaseHandler):
    '''Manipulates a specific submission state'''
    check_roles = 'admin'

    def put(self, submission_state_uuid, submission_substate_uuid):
        request = self.validate_message(self.request.content.read(),
                                        requests.SubmissionSubStateDesc)

        return update_submission_substate(self.request.tid, submission_state_uuid, submission_substate_uuid, request)

    @inlineCallbacks
    def delete(self, submission_state_uuid, submission_substate_uuid):
        yield retrieve_specific_submission_state(self.request.tid, submission_state_uuid)

        yield models.delete(models.SubmissionSubStates,
                            models.SubmissionSubStates.submissionstate_id == submission_state_uuid,
                            models.SubmissionSubStates.id == submission_substate_uuid)
