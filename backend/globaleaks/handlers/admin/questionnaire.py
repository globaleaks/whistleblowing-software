# -*- coding: utf-8
#
#   /admin/questionnaires
#   *****
# Implementation of the code executed on handler /admin/questionnaires
#
from twisted.internet.defer import inlineCallbacks, returnValue

from globaleaks import models, QUESTIONNAIRE_EXPORT_VERSION
from globaleaks.handlers.admin.step import db_create_step
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.public import serialize_questionnaire
from globaleaks.orm import transact
from globaleaks.rest import requests
from globaleaks.utils.structures import fill_localized_keys
from globaleaks.utils.utility import datetime_to_ISO8601, datetime_now


def db_get_questionnaire_list(session, tid, language):
    questionnaires = session.query(models.Questionnaire).filter(models.Questionnaire.tid.in_(set([1, tid])))

    return [serialize_questionnaire(session, tid, questionnaire, language) for questionnaire in questionnaires]


@transact
def get_questionnaire_list(session, tid, language):
    """
    Returns the questionnaire list.

    :param session: the session on which perform queries.
    :param language: the language in which to localize data.
    :return: a dictionary representing the serialization of the questionnaires.
    """
    return db_get_questionnaire_list(session, tid, language)


def db_get_questionnaire(session, tid, questionnaire_id, language):
    """
    Returns:
        (dict) the questionnaire with the specified id.
    """
    questionnaire = models.db_get(session, models.Questionnaire, models.Questionnaire.tid.in_(set([1, tid])), models.Questionnaire.id == questionnaire_id)

    return serialize_questionnaire(session, tid, questionnaire, language)


@transact
def get_questionnaire(session, tid, questionnaire_id, language):
    return db_get_questionnaire(session, tid, questionnaire_id, language)


def db_update_questionnaire(session, questionnaire, request, language):
    fill_localized_keys(request, models.Questionnaire.localized_keys, language)

    questionnaire.update(request)

    return questionnaire


def db_create_questionnaire(session, state, tid, questionnaire_dict, language):
    fill_localized_keys(questionnaire_dict, models.Questionnaire.localized_keys, language)

    questionnaire_dict['tid'] = tid
    q = models.db_forge_obj(session, models.Questionnaire, questionnaire_dict)

    for step in questionnaire_dict.get('steps', []):
        step['questionnaire_id'] = q.id
        db_create_step(session, tid, step, language)

    return q


@transact
def create_questionnaire(session, state, tid, request, language):
    """
    Creates a new questionnaire from the request of a client.

    Args:
        (dict) the request containing the keys to set on the model.

    Returns:
        (dict) representing the configured questionnaire
    """
    questionnaire = db_create_questionnaire(session, state, tid, request, language)

    return serialize_questionnaire(session, tid, questionnaire, language)


@transact
def update_questionnaire(session, tid, questionnaire_id, request, language):
    """
    Updates the specified questionnaire. If the key receivers is specified we remove
    the current receivers of the Questionnaire and reset set it to the new specified
    ones.

    Args:
        questionnaire_id:

        request:
            (dict) the request to use to set the attributes of the Questionnaire

    Returns:
            (dict) the serialized object updated
    """
    questionnaire = models.db_get(session, models.Questionnaire, models.Questionnaire.tid == tid, models.Questionnaire.id == questionnaire_id)

    questionnaire = db_update_questionnaire(session, questionnaire, request, language)

    return serialize_questionnaire(session, tid, questionnaire, language)


class QuestionnairesCollection(BaseHandler):
    check_roles = 'admin'
    cache_resource = True
    invalidate_cache = True

    def get(self):
        """
        Return all the questionnaires.
        """
        return get_questionnaire_list(self.request.tid, self.request.language)

    def post(self):
        """
        Create a new questionnaire.
        """
        validator = requests.AdminQuestionnaireDesc
        if self.request.language is None:
            validator = requests.AdminQuestionnaireDescRaw

        request = self.validate_message(self.request.content.read(), validator)

        return create_questionnaire(self.state, self.request.tid, request, self.request.language)


class QuestionnaireInstance(BaseHandler):
    check_roles = 'admin'
    invalidate_cache = True

    def put(self, questionnaire_id):
        """
        Update the specified questionnaire.
        """
        request = self.validate_message(self.request.content.read(),
                                        requests.AdminQuestionnaireDesc)

        return update_questionnaire(self.request.tid, questionnaire_id, request, self.request.language)

    def delete(self, questionnaire_id):
        """
        Delete the specified questionnaire.
        """
        return models.delete(models.Questionnaire, models.Questionnaire.tid == self.request.tid, models.Questionnaire.id == questionnaire_id)

    @inlineCallbacks
    def get(self, questionnaire_id):
        """
        Export questionnaire JSON
        """
        q = yield get_questionnaire(self.request.tid, questionnaire_id, None)
        q['export_date'] = datetime_to_ISO8601(datetime_now())
        q['export_version'] = QUESTIONNAIRE_EXPORT_VERSION
        returnValue(q)
