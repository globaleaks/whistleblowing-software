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
    GLSetting.gldb_path = 'db_test'    # path where check_db_files looks in
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), directory)
    for (path, dirs, files) in os.walk(path):
        for f in files:
            os.mkdir('db_test')
            dbpath = os.path.join(path, f)
            shutil.copyfile(dbpath, ('db_test/%s' % f))
            check_db_files()
            shutil.rmtree('db_test/')


class TestMigrationRoutines(helpers.TestGL):
    def test_migration_of_default_dbs(self):
        test_dbs_migration('db/empty')

    def test_migration_of_populated_dbs(self):
        test_dbs_migration('db/populated')
