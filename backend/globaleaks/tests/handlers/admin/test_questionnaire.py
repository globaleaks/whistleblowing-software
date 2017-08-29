# -*- coding: utf-8 -*-

from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.admin import questionnaire
from globaleaks.handlers.admin.questionnaire import get_questionnaire, create_questionnaire
from globaleaks.models import Questionnaire
from globaleaks.rest import errors
from globaleaks.tests import helpers


class TestQuestionnairesCollection(helpers.TestCollectionHandler):
    _handler = questionnaire.QuestionnairesCollection
    _test_desc = {
      'model': Questionnaire,
      'create': questionnaire.create_questionnaire,
      'data': {
        'name': 'test'
      }
    }


class TestQuestionnaireInstance(helpers.TestInstanceHandler):
    _handler = questionnaire.QuestionnaireInstance
    _test_desc = {
      'model': Questionnaire,
      'create': questionnaire.create_questionnaire,
      'data': {
        'name': 'test'
      }
    }
