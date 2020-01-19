# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks, returnValue

from globaleaks import models
from globaleaks.rest import errors
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.operation import OperationHandler
from globaleaks.models import fill_localized_keys, get_localized_values
from globaleaks.orm import transact, tw
from globaleaks.rest import requests


def serialize_submission_status(session, status, language):
    """Serializes a submission status into dictionary form for the client"""
    submission_status = {
        'id': status.id,
        'presentation_order': status.presentation_order,
        'substatuses': []
    }

    # See if we have any substatuses we need to serialize
    substatuses = session.query(models.SubmissionSubStatus) \
                         .filter(models.SubmissionSubStatus.tid == status.tid,
                                 models.SubmissionSubStatus.submissionstatus_id == status.id) \
                         .order_by(models.SubmissionSubStatus.presentation_order)

    for substatus in substatuses:
        submission_status['substatuses'].append(serialize_submission_substatus(substatus, language))

    return get_localized_values(submission_status, status, status.localized_keys, language)


def serialize_submission_substatus(substatus, language):
    """Serializes the submission's substatuses"""
    submission_substatus = {
        'id': substatus.id,
        'submissionstatus_id': substatus.submissionstatus_id,
        'presentation_order': substatus.presentation_order
    }

    return get_localized_values(submission_substatus, substatus, substatus.localized_keys, language)


def db_get_submission_statuses(session, tid, language):
    """Retrieves all submission statuses"""
    system_statuses = {}
    submission_statuses = []
    user_submission_statuses = []

    statuses = session.query(models.SubmissionStatus) \
                      .filter(models.SubmissionStatus.tid == tid) \
                      .order_by(models.SubmissionStatus.presentation_order)

    for status in statuses:
        status_dict = serialize_submission_status(session, status, language)
        if status.id in ['new', 'opened', 'closed']:
            system_statuses[status.id] = status_dict
        else:
            user_submission_statuses.append(status_dict)

    # Build the final array in the correct order
    submission_statuses.append(system_statuses['new'])
    submission_statuses.append(system_statuses['opened'])
    submission_statuses += user_submission_statuses
    submission_statuses.append(system_statuses['closed'])

    return submission_statuses


def db_get_submission_status(session, tid, submission_status_id, language):
    """Retrieves a specific status"""
    status = session.query(models.SubmissionStatus) \
                   .filter(models.SubmissionStatus.tid == tid,
                           models.SubmissionStatus.id == submission_status_id).one_or_none()

    if status is None:
        raise errors.ResourceNotFound

    return serialize_submission_status(session, status, language)


def db_update_status_model_from_request(model_obj, request, language):
    """Populates the model from the request, as well as setting default values"""
    fill_localized_keys(request, models.SubmissionStatus.localized_keys, language)
    model_obj.update(request)
    return model_obj


def db_create_submission_status(session, tid, request, language):
    """Creates submission status"""
    new_status = models.SubmissionStatus()
    new_status.tid = tid

    db_update_status_model_from_request(new_status, request, language)
    session.add(new_status)
    session.flush()

    return serialize_submission_status(session, new_status, language)


def db_update_submission_status(session, tid, submission_status_id, request, language):
    """Updates the submission status from request objects"""
    status = session.query(models.SubmissionStatus) \
                   .filter(models.SubmissionStatus.tid == tid,
                           models.SubmissionStatus.id == submission_status_id).one_or_none()

    if status is None:
        raise errors.ResourceNotFound

    db_update_status_model_from_request(status, request, language)


def db_update_substatus_model_from_request(model_obj, request, language):
    """Populates the model off each value from requests['substatus']"""
    fill_localized_keys(request, models.SubmissionSubStatus.localized_keys, language)
    model_obj.update(request)
    return model_obj


def db_update_submission_substatus(session, tid, submission_status_id, substatus_id, request, language):
    """Updates a substatus from a request object"""
    substatus = session.query(models.SubmissionSubStatus) \
                      .filter(models.SubmissionStatus.id == submission_status_id,
                              models.SubmissionStatus.tid == tid,
                              models.SubmissionSubStatus.submissionstatus_id == submission_status_id,
                              models.SubmissionSubStatus.id == substatus_id).one()

    if substatus is None:
        raise errors.ResourceNotFound

    db_update_substatus_model_from_request(substatus, request, language)


def db_create_submission_substatus(session, tid, submission_status_id, request, language):
    """Creates a substatus"""

    substatus_obj = models.SubmissionSubStatus()
    substatus_obj.tid = tid
    substatus_obj.submissionstatus_id = submission_status_id

    db_update_substatus_model_from_request(substatus_obj, request, language)

    session.add(substatus_obj)
    session.flush()

    return serialize_submission_substatus(substatus_obj, language)


@transact
def order_status_elements(session, handler, req_args, *args, **kwargs):
    """Sets the presentation order for status elements"""

    statuses = session.query(models.SubmissionStatus) \
                      .filter(models.SubmissionStatus.tid == handler.request.tid)

    id_dict = {status.id: status for status in statuses}
    ids = req_args['ids']

    for i, status_id in enumerate(ids):
        id_dict[status_id].presentation_order = i


@transact
def order_substatus_elements(session, handler, req_args, *args, **kwargs):
    """Sets presentation order for substatuses"""

    submission_status_id = args[0]

    substatuses = session.query(models.SubmissionSubStatus) \
                         .filter(models.SubmissionSubStatus.tid == self.request.tid,
                                 models.SubmissionSubStatus.submissionstatus_id == submission_status_id)

    id_dict = {substatus.id: substatus for substatus in substatuses}
    ids = req_args['ids']

    if len(ids) != len(id_dict) or set(ids) != set(id_dict):
        raise errors.InputValidationError('list does not contain all context ids')

    for i, substatus_id in enumerate(ids):
        id_dict[substatus_id].presentation_order = i


class SubmissionStatusCollection(OperationHandler):
    """Handles submission statuses on the backend"""
    check_roles = 'admin'
    invalidate_cache = True

    def get(self):
        return tw(db_get_submission_statuses, self.request.tid, self.request.language)

    def post(self):
        request = self.validate_message(self.request.content.read(),
                                        requests.SubmissionStatusDesc)

        return tw(db_create_submission_status, self.request.tid, request, self.request.language)

    def operation_descriptors(self):
        return {
            'order_elements': (order_status_elements, {'ids': [str]}),
        }


class SubmissionStatusInstance(BaseHandler):
    """Manipulates a specific submission status"""
    check_roles = 'admin'
    invalidate_cache = True

    def put(self, submission_status_id):
        request = self.validate_message(self.request.content.read(),
                                        requests.SubmissionStatusDesc)

        return tw(db_update_submission_status, self.request.tid, submission_status_id, request, self.request.language)

    def delete(self, submission_status_id):
        return models.delete(models.SubmissionStatus,
                             models.SubmissionStatus.tid == self.request.tid,
                             models.SubmissionStatus.id == submission_status_id)


class SubmissionSubStatusCollection(OperationHandler):
    """Manages substatuses for a given status"""
    check_roles = 'admin'
    invalidate_cache = True

    @inlineCallbacks
    def get(self, submission_status_id):
        submission_status = yield tw(db_get_submission_status,
                                     self.request.tid,
                                     submission_status_id,
                                     self.request.language)

        returnValue(submission_status['substatuses'])

    def post(self, submission_status_id):
        request = self.validate_message(self.request.content.read(),
                                        requests.SubmissionSubStatusDesc)

        return tw(db_create_submission_substatus, self.request.tid, submission_status_id, request, self.request.language)

    def operation_descriptors(self):
        return {
            'order_elements': (order_substatus_elements, {'ids': [str]}),
        }


class SubmissionSubStatusInstance(BaseHandler):
    """Manipulates a specific submission status"""
    check_roles = 'admin'
    invalidate_cache = True

    def put(self, submission_status_id, submission_substatus_id):
        request = self.validate_message(self.request.content.read(),
                                        requests.SubmissionSubStatusDesc)

        return tw(db_update_submission_substatus,
                  self.request.tid, submission_status_id,
                  submission_substatus_id,
                  request,
                  self.request.language)

    def delete(self, submission_status_id, submission_substatus_id):
        return models.delete(models.SubmissionSubStatus,
                            models.SubmissionSubStatus.tid == self.request.tid,
                            models.SubmissionSubStatus.id == submission_substatus_id,
                            models.SubmissionSubStatus.submissionstatus_id == submission_status_id)
