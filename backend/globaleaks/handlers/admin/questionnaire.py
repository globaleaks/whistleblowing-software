# -*- coding: UTF-8
#
#   /admin/questionnaires
#   *****
# Implementation of the code executed on handler /admin/questionnaires
#
import copy

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.orm import transact, transact_ro
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.admin.field import db_import_fields
from globaleaks.handlers.admin.step import db_create_step
from globaleaks.handlers.node import serialize_step, serialize_questionnaire
from globaleaks.rest import errors, requests
from globaleaks.rest.apicache import GLApiCache
from globaleaks.utils.structures import fill_localized_keys, get_localized_values
from globaleaks.utils.utility import log, datetime_now, datetime_to_ISO8601


@transact_ro
def get_questionnaire_list(store, language):
    """
    Returns the questionnaire list.

    :param store: the store on which perform queries.
    :param language: the language in which to localize data.
    :return: a dictionary representing the serialization of the questionnaires.
    """
    return [serialize_questionnaire(store, questionnaire, language)
        for questionnaire in store.find(models.Questionnaire)]


@transact_ro
def get_questionnaire(store, questionnaire_id, language):
    """
    Returns:
        (dict) the questionnaire with the specified id.
    """
    questionnaire = store.find(models.Questionnaire, models.Questionnaire.id == questionnaire_id).one()

    if not questionnaire:
        log.err("Requested invalid questionnaire")
        raise errors.QuestionnaireIdNotFound

    return serialize_questionnaire(store, questionnaire, language)


def db_get_default_questionnaire_id(store):
    return store.find(models.Questionnaire, models.Questionnaire.key == u'default').one().id


def db_get_questionnaire_steps(store, questionnaire_id, language):
    """
    Returns:
        (dict) the questionnaire associated with the questionnaire with the specified id.
    """
    questionnaire = store.find(models.Questionnaire, models.Questionnaire.id == questionnaire_id).one()

    if not questionnaire:
        log.err("Requested invalid questionnaire")
        raise errors.QuestionnaireIdNotFound

    return [serialize_step(store, s, language) for s in questionnaire.steps]


@transact_ro
def get_questionnaire_steps(*args):
    return db_get_questionnaire_steps(*args)


def fill_questionnaire_request(request, language):
    fill_localized_keys(request, models.Questionnaire.localized_keys, language)
    return request

def db_update_questionnaire(store, questionnaire, request, language):
    request = fill_questionnaire_request(request, language)

    questionnaire.update(request)

    return questionnaire


def db_create_steps(store, questionnaire, steps, language):
    """
    Create the specified steps
    :param store: the store on which perform queries.
    :param questionnaire: the questionnaire on which register specified steps.
    :param steps: a dictionary containing the new steps.
    :param language: the language of the specified steps.
    """
    for step in steps:
        step['questionnaire_id'] = questionnaire.id
        questionnaire.steps.add(db_create_step(store, step, language))


def db_create_questionnaire(store, request, language):
    request = fill_questionnaire_request(request, language)

    questionnaire = models.Questionnaire(request)

    store.add(questionnaire)

    return questionnaire


@transact
def create_questionnaire(store, request, language):
    """
    Creates a new questionnaire from the request of a client.

    We associate to the questionnaire the list of receivers and if the receiver is
    not valid we raise a ReceiverIdNotFound exception.

    Args:
        (dict) the request containing the keys to set on the model.

    Returns:
        (dict) representing the configured questionnaire
    """
    questionnaire = db_create_questionnaire(store, request, language)

    return serialize_questionnaire(store, questionnaire, language)


@transact
def update_questionnaire(store, questionnaire_id, request, language):
    """
    Updates the specified questionnaire. If the key receivers is specified we remove
    the current receivers of the Questionnaire and reset set it to the new specified
    ones.
    If no such questionnaire exists raises :class:`globaleaks.errors.QuestionnaireIdNotFound`.

    Args:
        questionnaire_id:

        request:
            (dict) the request to use to set the attributes of the Questionnaire

    Returns:
            (dict) the serialized object updated
    """
    questionnaire = store.find(models.Questionnaire, models.Questionnaire.id == questionnaire_id).one()
    if not questionnaire:
        raise errors.QuestionnaireIdNotFound

    questionnaire = db_update_questionnaire(store, questionnaire, request, language)

    return serialize_questionnaire(store, questionnaire, language)


@transact
def delete_questionnaire(store, questionnaire_id):
    """
    Deletes the specified questionnaire. If no such questionnaire exists raises
    :class:`globaleaks.errors.QuestionnaireIdNotFound`.

    Args:
        questionnaire_id: the questionnaire id of the questionnaire to remove.
    """
    questionnaire = store.find(models.Questionnaire, models.Questionnaire.id == questionnaire_id).one()
    if not questionnaire:
        log.err("Invalid questionnaire requested in removal")
        raise errors.QuestionnaireIdNotFound

    store.remove(questionnaire)


class QuestionnairesCollection(BaseHandler):
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def get(self):
        """
        Return all the questionnaires.

        Parameters: None
        Response: adminQuestionnaireList
        Errors: None
        """
        response = yield get_questionnaire_list(self.request.language)

        self.set_status(200)
        self.finish(response)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def post(self):
        """
        Create a new questionnaire.

        Request: AdminQuestionnaireDesc
        Response: AdminQuestionnaireDesc
        Errors: InvalidInputFormat, ReceiverIdNotFound
        """
        validator = requests.AdminQuestionnaireDesc if self.request.language is not None else requests.AdminQuestionnaireDescRaw

        request = self.validate_message(self.request.body, validator)

        response = yield create_questionnaire(request, self.request.language)

        GLApiCache.invalidate()

        self.set_status(201) # Created
        self.finish(response)


class QuestionnaireInstance(BaseHandler):
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def get(self, questionnaire_id):
        """
        Get the specified questionnaire.

        Parameters: questionnaire_id
        Response: AdminQuestionnaireDesc
        Errors: QuestionnaireIdNotFound, InvalidInputFormat
        """
        response = yield get_questionnaire(questionnaire_id, self.request.language)

        self.set_status(200)
        self.finish(response)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def put(self, questionnaire_id):
        """
        Update the specified questionnaire.

        Parameters: questionnaire_id
        Request: AdminQuestionnaireDesc
        Response: AdminQuestionnaireDesc
        Errors: InvalidInputFormat, QuestionnaireIdNotFound, ReceiverIdNotFound

        Updates the specified questionnaire.
        """
        request = self.validate_message(self.request.body,
                                        requests.AdminQuestionnaireDesc)

        response = yield update_questionnaire(questionnaire_id, request, self.request.language)
        GLApiCache.invalidate()

        self.set_status(202) # Updated
        self.finish(response)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def delete(self, questionnaire_id):
        """
        Delete the specified questionnaire.

        Request: AdminQuestionnaireDesc
        Response: None
        Errors: InvalidInputFormat, QuestionnaireIdNotFound
        """
        yield delete_questionnaire(questionnaire_id)
        GLApiCache.invalidate()

        self.set_status(200) # Ok and return no content
        self.finish()
