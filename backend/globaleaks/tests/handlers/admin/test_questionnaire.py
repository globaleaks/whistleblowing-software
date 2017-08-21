# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.admin import questionnaire
from globaleaks.handlers.admin.context import ContextInstance
from globaleaks.handlers.admin.questionnaire import get_questionnaire
from globaleaks.models import Questionnaire
from globaleaks.rest import errors
from globaleaks.tests import helpers
from globaleaks.tests.helpers import get_dummy_fieldoption_list

# special guest:
stuff = u"³²¼½¬¼³²"


class TestQuestionnaireCollection(helpers.TestHandler):
    _handler = questionnaire.QuestionnairesCollection

    def test_get(self):
        handler = self.request(role='admin')
        return handler.get()

    @inlineCallbacks
    def test_post(self):
        self.dummyQuestionnaire = yield get_questionnaire(u'default', 'en')
        self.dummyQuestionnaire['id'] = ''

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

    @inlineCallbacks
    def test_export_import(self):
        handler = self.request(role='admin')

        questionnaire = yield handler.get(self.dummyQuestionnaire['id'])

        questionnaire['name'] = 'testing_quests'

        questionnaire['steps'][0]['type'] = 'multichoice'
        questionnaire['steps'][0]['options'] = get_dummy_fieldoption_list()

        q_json = json.dumps(questionnaire)
        print '-. . .\nCOMMITING\n-. . .\n-. . .\n-. . .\n'

        yield handler.post(q_json)
