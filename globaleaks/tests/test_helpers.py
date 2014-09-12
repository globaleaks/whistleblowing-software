"""
Testandi ipsos testes.
"""
from __future__ import unicode_literals

import json
import os

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.tests import helpers


class TestFixtures(helpers.TestGL):

    @inlineCallbacks
    def test_import_fixture(self):
        """
        Make sure that every file in the fixtures path is correctly imported.
        """
        for root, dirs, files in os.walk(helpers.FIXTURES_PATH):
            for fixture in files:
                yield helpers.import_fixture(fixture)
                # XXX. what exately we do test here?

    def test_export_fixture(self):
        """
        After creating a mock model, test that all relevant informations are
        exported successfully.
        """
        class FakeModel(models.BaseModel):
            id = models.Int(primary=True)
            mockattr1 = models.Unicode()
            mockattr2 = models.Int()
            mockattr3 = models.Bool()

        m = FakeModel()
        m.mockattr1 = 'hello world!'
        m.mockattr2 = 1
        m.mockattr3 = True

        fixture = json.loads(helpers.export_fixture(m))
        self.assertEqual(len(fixture), 1)
        fixture, = fixture
        self.assertIn('class', fixture)
        self.assertIn('fields', fixture)
        self.assertIn('mockattr1', fixture['fields'])
        self.assertEqual(fixture['fields']['mockattr1'], 'hello world!')
        self.assertEqual(fixture['fields']['mockattr2'], 1)
        self.assertEqual(set(fixture['fields']),
                         {'id', 'mockattr1', 'mockattr2', 'mockattr3'})
