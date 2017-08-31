# -*- coding: utf-8 -*-
import json
import os

import sqlite3
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.admin import questionnaire
from globaleaks.handlers.admin.field import FieldCollection
from globaleaks.models import Questionnaire
from globaleaks.rest import errors
from globaleaks.rest.errors import InternalServerError
from globaleaks.tests import helpers
from globaleaks.utils.utility import read_json_file


class TestQuestionnairesCollection(helpers.TestCollectionHandler):
    _handler = questionnaire.QuestionnairesCollection
    _test_desc = {
      'model': Questionnaire,
      'create': questionnaire.create_questionnaire,
      'data': {
        'name': 'test'
      }
    }


    @inlineCallbacks
    def test_post_valid_json(self):
        self.test_data_dir = os.path.join(helpers.DATA_DIR, 'questionnaires')
        self.valid_files = [
            'normal.json',
            'normal-whistleblower-id.json',
            'normal-custom-template.json',
        ]

        for fname in self.valid_files:
            new_q = read_json_file(os.path.join(self.test_data_dir, 'valid', fname))

            if fname == 'normal-custom-template.json':
                template = read_json_file(os.path.join(self.test_data_dir, 'valid', 'custom_template.json'))
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
            ('malformed_opts.json', OverflowError),
            ('blank_ids.json', sqlite3.IntegrityError),
        ]

        for fname, err in invalid_test_cases:
            new_q = read_json_file(os.path.join(self.test_data_dir, 'invalid', fname))

            handler = self.request(new_q, role='admin')
            handler.request.language = None

            yield self.assertFailure(handler.post(), err)


class TestQuestionnaireInstance(helpers.TestInstanceHandler):
    _handler = questionnaire.QuestionnaireInstance
    _test_desc = {
      'model': Questionnaire,
      'create': questionnaire.create_questionnaire,
      'data': {
        'name': 'test'
      }
    }
