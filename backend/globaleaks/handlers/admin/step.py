# -*- coding: UTF-8
#
#   /admin/steps
#   *****
# Implementation of the code executed on handler /admin/steps
#
from storm.expr import Not, In

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.orm import transact, transact_ro
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.handlers.admin.field import db_create_field, db_update_field
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.node import serialize_step
from globaleaks.rest import requests, errors
from globaleaks.rest.apicache import GLApiCache
from globaleaks.utils.structures import fill_localized_keys


def db_create_step(store, step, language):
    """
    Create the specified step

    :param store: the store on which perform queries.
    :param language: the language of the specified steps.
    """
    fill_localized_keys(step, models.Step.localized_keys, language)

    s = models.Step.new(store, step)

    for c in step['children']:
        c['step_id'] = s.id
        db_create_field(store, c, language)

    return s


@transact
def create_step(store, step, language):
    """
    Transaction that perform db_create_step
    """
    return serialize_step(store, db_create_step(store, step, language), language)


def db_update_step(store, step_id, request, language):
    """
    Update the specified step with the details.
    raises :class:`globaleaks.errors.StepIdNotFound` if the step does
    not exist.

    :param store: the store on which perform queries.
    :param step_id: the step_id of the step to update
    :param request: the step definition dict
    :param language: the language of the step definition dict
    :return: a serialization of the object
    """
    step = models.Step.get(store, step_id)
    if not step:
        raise errors.StepIdNotFound

    fill_localized_keys(request, models.Step.localized_keys, language)

    step.update(request)

    for child in request['children']:
        db_update_field(store, child['id'], child, language)

    return step


@transact
def update_step(store, step_id, request, language):
    return serialize_step(store, db_update_step(store, step_id, request, language), language)


@transact_ro
def get_step(store, step_id, language):
    """
    Serialize the specified step

    :param store: the store on which perform queries.
    :param step_id: the id corresponding to the step.
    :param language: the language in which to localize data
    :return: the currently configured step.
    :rtype: dict
    """
    step = store.find(models.Step, models.Step.id == step_id).one()
    if not step:
        raise errors.StepIdNotFound

    return serialize_step(store, step, language)


@transact
def delete_step(store, step_id):
    """
    Delete the step object corresponding to step_id

    If the step has children, remove them as well.

    :param store: the store on which perform queries.
    :param step_id: the id corresponding to the step.
    :raises StepIdNotFound: if no such step is found.
    """
    step = store.find(models.Step, models.Step.id == step_id).one()
    if not step:
        raise errors.StepIdNotFound

    store.remove(step)


class StepCollection(BaseHandler):
    """
    Operation to create a step

    /admin/steps
    """
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def post(self):
        """
        Create a new step.

        :return: the serialized step
        :rtype: StepDesc
        :raises InvalidInputFormat: if validation fails.
        """
        request = self.validate_message(self.request.body,
                                        requests.AdminStepDesc)

        response = yield create_step(request, self.request.language)

        GLApiCache.invalidate('contexts')

        self.set_status(201)
        self.finish(response)


class StepInstance(BaseHandler):
    """
    Operation to iterate over a specific requested Step

    /admin/step
    """
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, step_id):
        """
        Get the step identified by step_id

        :param step_id:
        :return: the serialized step
        :rtype: StepDesc
        :raises StepIdNotFound: if there is no step with such id.
        :raises InvalidInputFormat: if validation fails.
        """
        response = yield get_step(step_id, self.request.language)

        self.set_status(200)
        self.finish(response)


    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def put(self, step_id):
        """
        Update attributes of the specified step

        :param step_id:
        :return: the serialized step
        :rtype: StepDesc
        :raises StepIdNotFound: if there is no step with such id.
        :raises InvalidInputFormat: if validation fails.
        """
        request = self.validate_message(self.request.body,
                                        requests.AdminStepDesc)

        response = yield update_step(step_id, request, self.request.language)

        GLApiCache.invalidate('contexts')

        self.set_status(202) # Updated
        self.finish(response)


    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def delete(self, step_id):
        """
        Delete the specified step.

        :param step_id:
        :raises StepIdNotFound: if there is no step with such id.
        :raises InvalidInputFormat: if validation fails.
        """
        yield delete_step(step_id)

        GLApiCache.invalidate('contexts')

        self.set_status(200)
