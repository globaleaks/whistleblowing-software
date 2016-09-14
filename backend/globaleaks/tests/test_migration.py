"""
Test database migrations.

for each version one an empty and a populated db must be stored in directories:
 - db/empty
 - db/populated
"""

import os
import shutil

from twisted.trial import unittest
from twisted.internet.defer import inlineCallbacks
from storm.locals import create_database, Store

from globaleaks import __version__, DATABASE_VERSION, FIRST_DATABASE_VERSION_SUPPORTED

from globaleaks.models import config, config_desc
from globaleaks.models.config_desc import GLConfig
from globaleaks import db
from globaleaks.settings import GLSettings
from globaleaks.tests.helpers import init_glsettings_for_unit_tests
from globaleaks.rest.errors import DatabaseIntegrityError


class TestMigrationRoutines(unittest.TestCase):
    def _test(self, path, f):
        init_glsettings_for_unit_tests()
        GLSettings.db_path = os.path.join(GLSettings.ramdisk_path, 'db_test')
        final_db_file = os.path.abspath(os.path.join(GLSettings.db_path, 'glbackend-%d.db' % DATABASE_VERSION))
        GLSettings.db_uri = GLSettings.make_db_uri(final_db_file)

        os.mkdir(GLSettings.db_path)
        dbpath = os.path.join(path, f)
        shutil.copyfile(dbpath, os.path.join(GLSettings.db_path, f))
        ret = db.manage_system_update()
        shutil.rmtree(GLSettings.db_path)
        self.assertNotEqual(ret, -1)

def test(path, f):
    return lambda self: self._test(path, f)

for directory in ['empty', 'populated']:
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'db', directory)
    for i in range(FIRST_DATABASE_VERSION_SUPPORTED, DATABASE_VERSION):
        setattr(TestMigrationRoutines, "test_%s_db_migration_%d" % (directory, i), test(path, 'glbackend-%d.db' % i))


class TestConfigUpdates(unittest.TestCase):
    def setUp(self):
        init_glsettings_for_unit_tests()

        GLSettings.db_path = os.path.join(GLSettings.ramdisk_path, 'db_test')
        os.mkdir(GLSettings.db_path)
        db_name = 'glbackend-%d.db' % DATABASE_VERSION
        db_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'db', 'populated', db_name)
        shutil.copyfile(db_path, os.path.join(GLSettings.db_path, db_name))

        db_file = os.path.join(GLSettings.db_path, db_name)
        GLSettings.db_uri = GLSettings.make_db_uri(db_file)

        self.store = Store(create_database(GLSettings.db_uri))

        # place a dummy version in the current db
        prv = config.PrivateFactory(self.store)
        self.dummy_ver = '2.XX.XX'
        prv.set_val('version', self.dummy_ver)
        self.assertEqual(prv.get_val('version'), self.dummy_ver)
        self.store.commit()

        # backup various mocks that we will use
        self._bck_f = config.is_cfg_valid
        GLConfig['private']['xx_smtp_password'] = GLConfig['private'].pop('smtp_password')
        self.dp = u'yes_you_really_should_change_me'

    def tearDown(self):
        shutil.rmtree(GLSettings.db_path)
        GLConfig['private']['smtp_password'] = GLConfig['private'].pop('xx_smtp_password')
        config.is_cfg_valid = self._bck_f

    def test_detect_and_fix_cfg_change(self):
        ret = config.is_cfg_valid(self.store)
        self.assertFalse(ret)

        config.manage_cfg_update(self.store)

        prv = config.PrivateFactory(self.store)
        self.assertEqual(prv.get_val('version'), __version__)
        self.assertEqual(prv.get_val('xx_smtp_password'), self.dp)

        ret = config.is_cfg_valid(self.store)
        self.assertTrue(ret)

    @inlineCallbacks
    def test_ver_change_success(self):
        yield db.manage_version_update()

        self.store = Store(create_database(GLSettings.db_uri))
        prv = config.PrivateFactory(self.store)
        self.assertEqual(prv.get_val('version'), __version__)

    @inlineCallbacks
    def test_ver_change_not_ok(self):
        # Set is_config_valid to false  during managed ver update
        config.is_cfg_valid = apply_gen(mod_bool)

        try:
            yield db.manage_version_update()
            self.fail()
        except DatabaseIntegrityError as e:
            self.assertIsInstance(e, DatabaseIntegrityError)

        # Ensure the rollback has succeeded
        prv = config.PrivateFactory(self.store)
        self.assertEqual(prv.get_val('version'), self.dummy_ver)

    @inlineCallbacks
    def test_ver_change_exception(self):
        # Explicity throw an exception in managed_ver_update via is_cfg_valid
        config.is_cfg_valid = apply_gen(throw_excep)

        try:
            yield db.manage_version_update()
            self.fail()
        except IOError as e:
            self.assertIsInstance(e, IOError)

        prv = config.PrivateFactory(self.store)
        self.assertEqual(prv.get_val('version'), self.dummy_ver)


def apply_gen(f):
    gen = f()

    def g(*args):
        return next(gen)

    return g

def throw_excep():
    yield True
    raise IOError('test throw up')

def mod_bool():
    i = 0
    while True:
        yield i % 2 == 0
        i += 1
