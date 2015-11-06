"""
Test database migrations.

for each version one an empty and a populated db must be stored in directories:
 - db/empty
 - db/populated

"""
import os
import shutil

from twisted.trial import unittest

from globaleaks.db import check_db_files
from globaleaks.settings import GLSettings
from globaleaks.tests.helpers import init_glsettings_for_unit_tests


def test_dbs_migration(directory):
    GLSettings.db_path = os.path.join(GLSettings.ramdisk_path, 'db_test')
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), directory)
    for (path, dirs, files) in os.walk(path):
        for f in files:
            os.mkdir(GLSettings.db_path)
            dbpath = os.path.join(path, f)
            shutil.copyfile(dbpath, ('%s/%s' % (GLSettings.db_path, f)))
            check_db_files()
            shutil.rmtree(GLSettings.db_path)


class TestMigrationRoutines(unittest.TestCase):
    def test_migration_of_default_dbs(self):
        init_glsettings_for_unit_tests()
        test_dbs_migration('db/empty')

    def test_migration_of_populated_dbs(self):
        init_glsettings_for_unit_tests()
        test_dbs_migration('db/populated')
