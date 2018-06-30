# Handle manipulation of submission states
from six import text_type

from twisted.internet.defer import inlineCallbacks, returnValue

from globaleaks import models
from globaleaks.rest import errors
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.operation import OperationHandler
from globaleaks.orm import transact
from globaleaks.rest import requests
from globaleaks.utils.structures import fill_localized_keys, get_localized_values

def serialize_submission_state(session, row, language):
    '''Serializes a submission state into dictionary form for the client'''
    submission_state = {
        'id': row.id,
        'tid': row.tid,
        'system_defined': row.system_defined,
        'system_usage': row.system_usage,
        'presentation_order': row.presentation_order,
        'substates': []
    }

    # See if we have any substates we need to serialize
    substate_rows = session.query(models.SubmissionSubState) \
                           .filter(models.SubmissionSubState.submissionstate_id == row.id) \
                           .order_by(models.SubmissionSubState.presentation_order)

    for substate_row in substate_rows:
        submission_state['substates'].append(
            serialize_submission_substate(substate_row, language)
        )

    return get_localized_values(submission_state, row, row.localized_keys, language)


def serialize_submission_substate(row, language):
    '''Serializes the submission's substates'''
    submission_substate = {
        'id': row.id,
        'submissionstate_id': row.submissionstate_id,
        'presentation_order': row.presentation_order
    }

    return get_localized_values(submission_substate, row, row.localized_keys, language)


def db_retrieve_all_submission_states(session, tid, language):
    '''Retrieves all submission states'''
    system_states = {}
    submission_states = []
    user_submission_states = []

    rows = session.query(models.SubmissionState) \
                  .filter(models.SubmissionState.tid == tid) \
                  .order_by(models.SubmissionState.presentation_order)

    for row in rows:
        if row.system_defined is False:
            user_submission_states.append(
                serialize_submission_state(session, row, language)
            )
        else:
            system_states[row.system_usage] = serialize_submission_state(session, row, language)

    # Build the final array in the correct order
    submission_states.append(system_states['new'])
    submission_states.append(system_states['open'])
    submission_states += user_submission_states
    submission_states.append(system_states['closed'])

    return submission_states


@transact
def retrieve_all_submission_states(session, tid, language):
    '''Transact version of db_retrieve_all_submission_states'''
    return db_retrieve_all_submission_states(session, tid, language)


def db_retrieve_specific_submission_state(session, tid, submission_state_uuid, language):
    '''Retrieves a specific state serialized as a rows'''
    state = session.query(models.SubmissionState) \
                   .filter(models.SubmissionState.tid == tid, \
                           models.SubmissionState.id == submission_state_uuid).one_or_none()

    if state is None:
        raise errors.ResourceNotFound

    return serialize_submission_state(session, state, language)


@transact
def retrieve_specific_submission_state(session, tid, submission_state_uuid, language):
    '''Transact version of db_retrieve_specific_submission_state'''
    return db_retrieve_specific_submission_state(session, tid, submission_state_uuid, language)


def update_state_model_from_request(model_obj, request, language):
    '''Populates the model from the request, as well as setting default values'''
    fill_localized_keys(request, models.SubmissionState.localized_keys, language)

    model_obj.label = request['label']
    model_obj.presentation_order = request['presentation_order']
    return model_obj


@transact
def create_submission_state(session, tid, request, language):
    '''Creates submission state'''
    new_state = models.SubmissionState()
    new_state.tid = tid
    update_state_model_from_request(new_state, request, language)

    session.add(new_state)
    session.flush()

    return serialize_submission_state(session, new_state, language)


@transact
def update_submission_state(session, tid, submission_state_uuid, request, language):
    '''Updates the submission state from request objects'''
    state = session.query(models.SubmissionState) \
                   .filter(models.SubmissionState.tid == tid, \
                           models.SubmissionState.id == submission_state_uuid).one_or_none()

    if state is None:
        raise errors.ResourceNotFound

    state = update_state_model_from_request(state, request, language)
    session.merge(state)


@transact
def get_id_for_system_state(session, tid, system_state):
    '''Returns the ID of a system defined state'''
    return db_get_id_for_system_state(session, tid, system_state)


def db_get_id_for_system_state(session, tid, system_state):
    '''Returns the UUID of a given submission state'''
    state = session.query(models.SubmissionState) \
                   .filter(models.SubmissionState.tid == tid, \
                           models.SubmissionState.system_usage == system_state).one_or_none()

    if state is None:
        raise errors.ResourceNotFound

    return state.id


@transact
def get_submission_state(session, tid, submission_state_uuid):
    '''Returns the UUID of a given submission state'''
    state = session.query(models.SubmissionState) \
                   .filter(models.SubmissionState.tid == tid, \
                           models.SubmissionState.id == submission_state_uuid).one_or_none()

    if state is None:
        raise errors.ResourceNotFound

    return state


def update_substate_model_from_request(model_obj, request, language):
    '''Populates the model off each value from requests['substate']'''
    fill_localized_keys(request, models.SubmissionSubState.localized_keys, language)

    model_obj.label = request['label']
    model_obj.presentation_order = request['presentation_order']
    return model_obj


@transact
def update_submission_substate(session, tid, submission_state_uuid, substate_uuid, request, language):
    '''Updates a substate from a request object'''
    substate = session.query(models.SubmissionSubState) \
                      .filter(models.SubmissionState.id == submission_state_uuid,
                              models.SubmissionState.tid == tid,
                              models.SubmissionSubState.submissionstate_id == submission_state_uuid,
                              models.SubmissionSubState.id == substate_uuid).one()

    if substate is None:
        raise errors.ResourceNotFound

    substate = update_substate_model_from_request(substate, request, language)
    session.merge(substate)


@transact
def create_submission_substate(session, tid, submission_state_uuid, request, language):
    '''Creates a substate'''

    # Safety check here, make sure that the submission state we're looking for
    # 1. exists
    # 2. is part of our tid
    db_retrieve_specific_submission_state(session, tid, submission_state_uuid, language)

    substate_obj = models.SubmissionSubState()
    substate_obj.submissionstate_id = submission_state_uuid

    update_substate_model_from_request(substate_obj, request, language)

    session.add(substate_obj)
    session.flush()

    return serialize_submission_substate(substate_obj, language)


@transact
def order_state_elements(session, handler, req_args, *args, **kwargs):
    '''Sets the presentation order for state elements'''

    # Presentation order is ignored for states
    states = session.query(models.SubmissionState)\
                    .filter(models.SubmissionState.tid == handler.request.tid,
                            models.SubmissionState.system_defined == False)

    id_dict = {state.id: state for state in states}
    ids = req_args['ids']

    if len(ids) != len(id_dict) or set(ids) != set(id_dict):
        raise errors.InputValidationError('list does not contain all context ids')

    for i, state_id in enumerate(ids):
        id_dict[state_id].presentation_order = i


@transact
def order_substate_elements(session, handler, req_args, *args, **kwargs):
    '''Sets presentation order for substates'''

    submission_state_id = args[0]

    substates = session.query(models.SubmissionSubState)\
                       .filter(models.SubmissionSubState.submissionstate_id == submission_state_id)

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
        return retrieve_all_submission_states(self.request.tid, self.request.language)

    def post(self):
        request = self.validate_message(self.request.content.read(),
                                        requests.SubmissionStateDesc)

        return create_submission_state(self.request.tid, request, self.request.language)

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

        return update_submission_state(self.request.tid, submission_state_uuid, request, self.request.language)

    def delete(self, submission_state_uuid):
        return models.delete(models.SubmissionState,
                             models.SubmissionState.tid == self.request.tid,
                             models.SubmissionState.id == submission_state_uuid)


class SubmissionSubStateCollection(OperationHandler):
    '''Manages substates for a given state'''
    check_roles = 'admin'

    @inlineCallbacks
    def get(self, submission_state_uuid):
        submission_state = yield retrieve_specific_submission_state(self.request.tid, submission_state_uuid, self.request.language)

        returnValue(submission_state['substates'])

    def post(self, submission_state_uuid):
        request = self.validate_message(self.request.content.read(),
                                        requests.SubmissionSubStateDesc)

        return create_submission_substate(self.request.tid, submission_state_uuid, request, self.request.language)

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

        return update_submission_substate(self.request.tid, submission_state_uuid, submission_substate_uuid, request, self.request.language)

    @inlineCallbacks
    def delete(self, submission_state_uuid, submission_substate_uuid):
        yield retrieve_specific_submission_state(self.request.tid, submission_state_uuid, self.request.language)

        yield models.delete(models.SubmissionSubState,
                            models.SubmissionSubState.submissionstate_id == submission_state_uuid,
                            models.SubmissionSubState.id == submission_substate_uuid)