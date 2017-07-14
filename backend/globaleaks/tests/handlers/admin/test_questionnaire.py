# -*- coding: utf-8 -*-
import json

from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.admin import questionnaire
from globaleaks.handlers.admin.context import ContextInstance
from globaleaks.models import Questionnaire
from globaleaks.rest import requests, errors
from globaleaks.tests import helpers

# special guest:
stuff = u"³²¼½¬¼³²"


class TestQuestionnaireCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = questionnaire.QuestionnairesCollection

    def test_get(self):
        handler = self.request(role='admin')
        return handler.get()

    @inlineCallbacks
    def test_post(self):
        for attrname in Questionnaire.unicode_keys:
            self.dummyQuestionnaire[attrname] = stuff

        handler = self.request(self.dummyQuestionnaire, role='admin')
        response = yield handler.post()

        for attrname in Questionnaire.unicode_keys:
            self.assertEqual(response[attrname], stuff)


class TestQuestionnaireInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = questionnaire.QuestionnaireInstance

    @inlineCallbacks
    def test_put(self):
        for attrname in Questionnaire.unicode_keys:
            self.dummyQuestionnaire[attrname] = stuff

        handler = self.request(self.dummyQuestionnaire, role='admin')
        response = yield handler.put(self.dummyQuestionnaire['id'])

        for attrname in Questionnaire.unicode_keys:
            self.assertEqual(response[attrname], stuff)

    @inlineCallbacks
    def test_delete(self):
        handler = self.request(self.dummyQuestionnaire, role='admin')
        ctx_handler = self.request({}, handler_cls=ContextInstance, role='admin')
        yield ctx_handler.delete(self.dummyContext['id'])
        yield handler.delete(self.dummyQuestionnaire['id'])
        yield self.assertFailure(handler.delete(self.dummyQuestionnaire['id']),
                                 errors.QuestionnaireIdNotFound)
