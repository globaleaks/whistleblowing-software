"""
Test database migrations.

for each version one an empty and a populated db must be sessiond in directories:
 - db/empty
 - db/populated
"""
import filecmp
import os
import shutil

from twisted.trial import unittest

from globaleaks import DATABASE_VERSION, FIRST_DATABASE_VERSION_SUPPORTED, models
from globaleaks.db import update_db
from globaleaks.db.migrations import update_37, update_50
from globaleaks.models import config
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

    def test_db_migration_failure_inside(self):
        # This tests verify that an exception happeing inside a migration causes the
        # migration to fail and that on this condition the database results unmodified.
        def epilogue(self):
            raise Exception('failure')

        update_50.MigrationScript.epilogue = epilogue

        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'db', 'populated')

        helpers.init_state()
        self.db_path = os.path.join(Settings.working_path, 'db')
        self.final_db_file = os.path.abspath(os.path.join(Settings.working_path, 'globaleaks.db'))

        set_db_uri('sqlite:' + self.final_db_file)

        shutil.rmtree(self.db_path, True)
        os.mkdir(self.db_path)
        srcdb = os.path.join(path, 'glbackend-49.db')
        dstdb = os.path.join(Settings.working_path, 'globaleaks.db')

        shutil.copyfile(srcdb, dstdb)

        ret = update_db()

        self.assertEqual(ret, -1)

        self.assertTrue(filecmp.cmp(srcdb, dstdb))


def test(path, version):
    return lambda self: self._test(path, version)


path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'db', 'populated')
for i in range(FIRST_DATABASE_VERSION_SUPPORTED, DATABASE_VERSION):
    setattr(TestMigrationRoutines, "test_db_migration_%d" % i, test(path, i))
