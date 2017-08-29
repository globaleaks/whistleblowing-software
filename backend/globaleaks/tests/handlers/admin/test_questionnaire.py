# -*- coding: utf-8 -*-
import exceptions
import json
import os

import sqlite3
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.admin import questionnaire
from globaleaks.handlers.admin.context import ContextInstance
from globaleaks.handlers.admin.questionnaire import get_questionnaire
from globaleaks.handlers.admin.field import FieldCollection
from globaleaks.models import Questionnaire
from globaleaks.rest import errors
from globaleaks.rest.errors import InternalServerError
from globaleaks.tests import helpers

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

        self.dummyQuestionnaire['steps'] = []

        handler = self.request(self.dummyQuestionnaire, role='admin')
        response = yield handler.post()

        for attrname in Questionnaire.unicode_keys:
            self.assertEqual(response[attrname], stuff)

    @inlineCallbacks
    def test_post_valid_json(self):
        self.test_data_dir = os.path.join(helpers.DATA_DIR, 'questionnaires')
        self.valid_files = [
            'normal.json',
            'normal-whistleblower-id.json',
            'normal-custom-template.json',
        ]

        for fname in self.valid_files:
            p = os.path.join(self.test_data_dir, 'valid', fname)
            with open(p) as f:
                new_q = json.loads(f.read())

            if fname == 'normal-custom-template.json':
                with open(os.path.join(self.test_data_dir, 'valid', 'custom_template.json')) as f:
                    template = json.loads(f.read())
                h = self.request(template, role='admin', handler_cls=FieldCollection)
                res = yield h.post()

            handler = self.request(new_q, role='admin')
            handler.request.language = None

            resp_q = yield handler.post()
            resp_q = json.loads(json.dumps(resp_q))

            new_q.pop('export_date')
            new_q.pop('export_version')
            self.assertEqual(new_q, resp_q)

    @inlineCallbacks
    def test_post_invalid_json(self):
        self.test_data_dir = os.path.join(helpers.DATA_DIR, 'questionnaires')

        invalid_test_cases = [
            ('cyclic_groupid.json', errors.InvalidInputFormat),
            ('duplicate_ids.json', sqlite3.IntegrityError),
            ('malformed_ids.json', sqlite3.IntegrityError),
            ('malformed_attrs.json', sqlite3.IntegrityError),
            ('malformed_opts.json', exceptions.OverflowError),
            ('blank_ids.json', sqlite3.IntegrityError),
        ]

        for fname, err in invalid_test_cases:
            p = os.path.join(self.test_data_dir, 'invalid', fname)
            with open(p) as f:
                new_q = json.loads(f.read())

            handler = self.request(new_q, role='admin')
            handler.request.language = None

            yield self.assertFailure(handler.post(), err)


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
