# -*- coding: utf-8 -*-
import random
import json

from twisted.internet.defer import inlineCallbacks

from globaleaks import __version__
from globaleaks.rest.errors import InvalidInputFormat
from globaleaks.tests import helpers
from globaleaks.rest import requests, errors
from globaleaks.handlers.admin import questionnaire
from globaleaks.models import Questionnaire

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
        yield handler.post()

        for attrname in Questionnaire.unicode_keys:
            self.assertEqual(self.responses[0][attrname], stuff)


class TestQuestionnaireInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = questionnaire.QuestionnaireInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        yield handler.get(self.dummyQuestionnaire['id'])
        self._handler.validate_message(json.dumps(self.responses[0]), requests.AdminQuestionnaireDesc)

    @inlineCallbacks
    def test_put(self):
        for attrname in Questionnaire.unicode_keys:
            self.dummyQuestionnaire[attrname] = stuff

        handler = self.request(self.dummyQuestionnaire, role='admin')
        yield handler.put(self.dummyQuestionnaire['id'])

        for attrname in Questionnaire.unicode_keys:
            self.assertEqual(self.responses[0][attrname], stuff)

    @inlineCallbacks
    def test_delete(self):
        handler = self.request(self.dummyQuestionnaire, role='admin')
        yield handler.delete(self.dummyQuestionnaire['id'])
        yield self.assertFailure(handler.get(self.dummyQuestionnaire['id']),
                                 errors.QuestionnaireIdNotFound)
