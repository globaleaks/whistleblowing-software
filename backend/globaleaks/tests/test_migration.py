"""
Test database migrations.

for each version one an empty and a populated db must be stored in directories:
 - db/empty
 - db/populated

"""
import os
import shutil

from twisted.trial import unittest

from globaleaks import DATABASE_VERSION, FIRST_DATABASE_VERSION_SUPPORTED

from globaleaks.db import check_db_files
from globaleaks.settings import GLSettings
from globaleaks.tests.helpers import init_glsettings_for_unit_tests


class TestMigrationRoutines(unittest.TestCase):
    def _test(self, path, f):
        init_glsettings_for_unit_tests()
        GLSettings.db_path = os.path.join(GLSettings.ramdisk_path, 'db_test')
        os.mkdir(GLSettings.db_path)
        dbpath = os.path.join(path, f)
        shutil.copyfile(dbpath, '%s/%s' % (GLSettings.db_path, f))
        ret = check_db_files()
        shutil.rmtree(GLSettings.db_path)
        self.assertNotEqual(ret, -1)

def test(path, f):
    return lambda self: self._test(path, f)

for directory in ['empty', 'populated']:
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'db', directory)
    for i in range(FIRST_DATABASE_VERSION_SUPPORTED, DATABASE_VERSION):
        setattr(TestMigrationRoutines, "test_%s_db_migration_%d" % (directory, i), test(path, 'glbackend-%d.db' % i))
