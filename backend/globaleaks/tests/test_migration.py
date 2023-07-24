"""
Test database migrations.

for each version one an empty and a populated db must be sessiond in directories:
 - db/empty
 - db/populated
"""
import os
import shutil

from twisted.trial import unittest

from globaleaks import DATABASE_VERSION, FIRST_DATABASE_VERSION_SUPPORTED
from globaleaks.db import update_db
from globaleaks.orm import set_db_uri
from globaleaks.settings import Settings
from globaleaks.tests import helpers


class TestMigrationRoutines(unittest.TestCase):
    def _test(self, path, version):
        helpers.init_state()
        srcpath = os.path.join(path, 'globaleaks-%d.db' % version)
        dstpath = os.path.join(Settings.working_path, 'globaleaks.db')
        shutil.copyfile(srcpath, dstpath)

        # TESTS PRECONDITIONS
        preconditions = getattr(self, 'preconditions_%d' % version, None)
        if preconditions is not None:
            preconditions()

        ret = update_db()

        # TESTS POSTCONDITIONS
        postconditions = getattr(self, 'postconditions_%d' % version, None)
        if postconditions is not None:
            postconditions()

        self.assertNotEqual(ret, -1)


def test(path, version):
    return lambda self: self._test(path, version)


path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'db', 'populated')


for i in range(FIRST_DATABASE_VERSION_SUPPORTED, DATABASE_VERSION + 1):
    setattr(TestMigrationRoutines, "test_db_migration_%d" % i, test(path, i))
