# -*- coding: utf-8 -*-
import os

from sqlalchemy.exc import IntegrityError

from twisted.python import failure
from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.orm import transact
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
            ('cyclic_groupid.json', errors.InputValidationError),
            ('duplicate_ids.json', IntegrityError)
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


class TestQuestionnareDuplication(helpers.TestHandlerWithPopulatedDB):
    _handler = questionnaire.QuestionnareDuplication

    @transact
    def get_questionnare_count(self, session):
        """Gets a count of the questionnaires"""
        return session.query(models.Questionnaire).count()

    @transact
    def get_new_questionnare(self, session):
        """Returns first questionnare ID"""
        questionnare_obj = session.query(models.Questionnaire).filter(
            models.Questionnaire.id != u'default').first()
        session.expunge(questionnare_obj)
        return questionnare_obj

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)

    @inlineCallbacks
    def test_duplicate_questionnaire(self):
        # Sanity check our base behavior
        questionnaire_count = yield self.get_questionnare_count()
        self.assertEqual(questionnaire_count, 1)

        data_request = {
            'questionnaire_id': 'default',
            'new_name': 'Duplicated Default'
        }

        handler = self.request(data_request, role='admin')
        response = yield handler.post()

        questionnaire_count = yield self.get_questionnare_count()
        self.assertEqual(questionnaire_count, 2)

        new_questionnare = yield self.get_new_questionnare()
        self.assertEqual(new_questionnare.name, 'Duplicated Default')
