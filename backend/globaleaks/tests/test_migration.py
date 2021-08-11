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
        f = 'glbackend-%d.db' % version

        helpers.init_state()
        self.db_path = os.path.join(Settings.working_path, 'db')
        self.final_db_file = os.path.abspath(os.path.join(Settings.working_path, 'globaleaks.db'))

        set_db_uri('sqlite:' + self.final_db_file)

        shutil.rmtree(self.db_path, True)
        os.mkdir(self.db_path)
        dbpath = os.path.join(path, f)
        if version < 41:
            dbfile = os.path.join(self.db_path, f)
            Settings.db_file_path = os.path.join(Settings.working_path, 'db', 'glbackend-%d.db' % version)
        else:
            dbfile = os.path.join(Settings.working_path, 'globaleaks.db')

        shutil.copyfile(dbpath, dbfile)

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
for i in range(FIRST_DATABASE_VERSION_SUPPORTED, DATABASE_VERSION):
    setattr(TestMigrationRoutines, "test_db_migration_%d" % i, test(path, i))
