# -*- coding: utf-8 -*-
import os

import sqlite3
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.admin import questionnaire
from globaleaks.models import Questionnaire
from globaleaks.rest import errors
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
    def test_post_invalid_json(self):
        self.test_data_dir = os.path.join(helpers.DATA_DIR, 'questionnaires')

        invalid_test_cases = [
            ('cyclic_groupid.json', errors.InvalidInputFormat),
            ('duplicate_ids.json', sqlite3.IntegrityError),
            ('malformed_ids.json', sqlite3.IntegrityError),
            ('malformed_attrs.json', sqlite3.IntegrityError),
            ('blank_ids.json', sqlite3.IntegrityError),
        ]

        for fname, err in invalid_test_cases:
            new_q = read_json_file(os.path.join(self.test_data_dir, fname))

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
