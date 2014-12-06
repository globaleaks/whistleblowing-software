"""
Test database migrations.

The following are the last tags for each db version:
 5   2.24.8
 6  2.27.24
 7   2.30.1
 8   2.50.8
 9   2.52.3
10   2.54.4
11  2.54.16

for each version one an empty and a populated db must be stored in directories:
 - db/empty
 - db/populated

"""
from __future__ import with_statement

from cStringIO import StringIO
import os
import shutil

from mock import patch
from globaleaks.tests import helpers
from globaleaks.db import base_updater, check_db_files
from globaleaks.settings import GLSetting

skip = 'Skipped due to #1044'


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
    @patch('sys.stdout', new_callable=StringIO)
    def test_migration_of_default_dbs(self, log):
        test_dbs_migration('db/empty')

    @patch('sys.stdout', new_callable=StringIO)
    def test_migration_of_populated_dbs(self, log):
        test_dbs_migration('db/populated')
