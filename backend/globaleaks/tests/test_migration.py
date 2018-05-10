"""
Test database migrations.

for each version one an empty and a populated db must be sessiond in directories:
 - db/empty
 - db/populated
"""
import os
import shutil

from sqlalchemy.orm import sessionmaker

from globaleaks import __version__, DATABASE_VERSION, FIRST_DATABASE_VERSION_SUPPORTED, models
from globaleaks.db import migration, update_db
from globaleaks.db.migrations import update_37
from globaleaks.models import config
from globaleaks.orm import get_session, make_db_uri, set_db_uri
from globaleaks.rest import errors
from globaleaks.settings import Settings
from globaleaks.tests import helpers
from twisted.trial import unittest


class TestMigrationRoutines(unittest.TestCase):
    def _test(self, path, version):
        f = 'glbackend-%d.db' % version

        helpers.init_state()
        self.db_path = os.path.join(Settings.working_path, 'db')
        Settings.db_file_path = os.path.join(Settings.working_path, 'db', 'glbackend-%d.db' % version)
        self.final_db_file = os.path.abspath(os.path.join(Settings.working_path, 'globaleaks.db'))

        set_db_uri('sqlite:' + self.final_db_file)

        shutil.rmtree(self.db_path, True)
        os.mkdir(self.db_path)
        dbpath = os.path.join(path, f)
        dbfile = os.path.join(self.db_path, f)
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

        #shutil.rmtree(self.db_path, True)
        self.assertNotEqual(ret, -1)

    def preconditions_30(self):
        logo_path = os.path.join(Settings.files_path, 'logo.png')
        css_path = os.path.join(Settings.files_path, 'custom_stylesheet.css')

        shutil.copy(os.path.join(helpers.DATA_DIR, 'tor/private_key'), logo_path)
        shutil.copy(os.path.join(helpers.DATA_DIR, 'tor/hostname'), css_path)

    def postconditions_30(self):
        session = get_session(make_db_uri(self.final_db_file))
        self.assertTrue(session.query(models.File).filter(models.File.id == u'logo').count() == 1)
        self.assertTrue(session.query(models.File).filter(models.File.id == u'css').count() == 1)
        session.close()

    def preconditions_36(self):
        update_37.TOR_DIR = Settings.working_path

        pk_path = os.path.join(update_37.TOR_DIR, 'private_key')
        hn_path = os.path.join(update_37.TOR_DIR, 'hostname')

        shutil.copy(os.path.join(helpers.DATA_DIR, 'tor/private_key'), pk_path)
        shutil.copy(os.path.join(helpers.DATA_DIR, 'tor/hostname'), hn_path)

    def postconditions_36(self):
        session = get_session(make_db_uri(self.final_db_file))

        hs = session.query(config.Config).filter(config.Config.tid == 1, config.Config.var_name == u'onionservice').one().value
        pk = session.query(config.Config).filter(config.Config.tid == 1, config.Config.var_name == u'tor_onion_key').one().value

        self.assertEqual('lftx7dbyvlc5txtl.onion', hs)
        with open(os.path.join(helpers.DATA_DIR, 'tor/ephemeral_service_key')) as f:
            saved_key = f.read().strip()

        self.assertEqual(saved_key, pk)
        session.close()


def test(path, version):
    return lambda self: self._test(path, version)


for directory in ['populated']:
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'db', directory)
    for i in range(FIRST_DATABASE_VERSION_SUPPORTED, DATABASE_VERSION):
        setattr(TestMigrationRoutines, "test_%s_db_migration_%d" % (directory, i), test(path, i))
