"""
Test database migrations.

for each version one an empty and a populated db must be stored in directories:
 - db/empty
 - db/populated

"""
from __future__ import with_statement

import shutil

import os
from globaleaks.tests import helpers
from globaleaks.db import check_db_files
from globaleaks.settings import GLSetting


def test_dbs_migration(directory):
    GLSetting.gldb_path = os.path.join(GLSetting.ramdisk_path, 'db_test')
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), directory)
    for (path, dirs, files) in os.walk(path):
        for f in files:
            os.mkdir(GLSetting.gldb_path)
            dbpath = os.path.join(path, f)
            shutil.copyfile(dbpath, ('%s/%s' % (GLSetting.gldb_path, f)))
            check_db_files()
            shutil.rmtree(GLSetting.gldb_path)


class TestMigrationRoutines(helpers.TestGL):
    def test_migration_of_default_dbs(self):
        test_dbs_migration('db/empty')

    def test_migration_of_populated_dbs(self):
        test_dbs_migration('db/populated')
