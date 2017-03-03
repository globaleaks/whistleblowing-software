"""
Test database migrations.

for each version one an empty and a populated db must be stored in directories:
 - db/empty
 - db/populated
"""

import os
import shutil

from storm.locals import create_database, Store
from twisted.trial import unittest

from globaleaks import __version__, DATABASE_VERSION, FIRST_DATABASE_VERSION_SUPPORTED
from globaleaks.db import migration, perform_system_update
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.handlers.admin.field import db_create_field
from globaleaks.models import config, Field
from globaleaks.models.config_desc import GLConfig
from globaleaks.models.l10n import EnabledLanguage, NotificationL10NFactory
from globaleaks.settings import GLSettings
from globaleaks.tests import helpers, config as test_config
from globaleaks.rest import errors


class TestMigrationRoutines(unittest.TestCase):

    def setUp(self):
        test_config.skipIf('migration')

    def _test(self, path, f):
        helpers.init_glsettings_for_unit_tests()
        GLSettings.db_path = os.path.join(GLSettings.ramdisk_path, 'db_test')
        final_db_file = os.path.abspath(os.path.join(GLSettings.db_path, 'glbackend-%d.db' % DATABASE_VERSION))
        GLSettings.db_uri = GLSettings.make_db_uri(final_db_file)

        shutil.rmtree(GLSettings.db_path)
        os.mkdir(GLSettings.db_path)
        dbpath = os.path.join(path, f)
        dbfile = os.path.join(GLSettings.db_path, f)
        shutil.copyfile(dbpath, dbfile)
        ret = perform_system_update()
        shutil.rmtree(GLSettings.db_path)
        self.assertNotEqual(ret, -1)


def test(path, f):
    return lambda self: self._test(path, f)


for directory in ['populated']:
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'db', directory)
    for i in range(FIRST_DATABASE_VERSION_SUPPORTED, DATABASE_VERSION):
        setattr(TestMigrationRoutines, "test_%s_db_migration_%d" % (directory, i), test(path, 'glbackend-%d.db' % i))


class TestConfigUpdates(unittest.TestCase):
    def setUp(self):
        helpers.init_glsettings_for_unit_tests()

        GLSettings.db_path = os.path.join(GLSettings.ramdisk_path, 'db_test')
        os.mkdir(GLSettings.db_path)
        db_name = 'glbackend-%d.db' % DATABASE_VERSION
        db_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'db', 'populated', db_name)
        shutil.copyfile(db_path, os.path.join(GLSettings.db_path, db_name))

        self.db_file = os.path.join(GLSettings.db_path, db_name)
        GLSettings.db_uri = GLSettings.make_db_uri(self.db_file)

        # place a dummy version in the current db
        store = Store(create_database(GLSettings.db_uri))
        prv = config.PrivateFactory(store)
        self.dummy_ver = '2.XX.XX'
        prv.set_val('version', self.dummy_ver)
        self.assertEqual(prv.get_val('version'), self.dummy_ver)
        store.commit()
        store.close()

        # backup various mocks that we will use
        self._bck_f = config.is_cfg_valid
        GLConfig['private']['xx_smtp_password'] = GLConfig['private'].pop('smtp_password')
        self.dp = u'yes_you_really_should_change_me'

    def tearDown(self):
        shutil.rmtree(GLSettings.db_path)
        GLConfig['private']['smtp_password'] = GLConfig['private'].pop('xx_smtp_password')
        config.is_cfg_valid = self._bck_f

    def test_migration_error_with_removed_language(self):
        store = Store(create_database(GLSettings.db_uri))
        zyx = EnabledLanguage('zyx')
        store.add(zyx)
        store.commit()
        store.close()

        self.assertRaises(Exception, migration.perform_data_update, self.db_file)

    def test_detect_and_fix_cfg_change(self):
        store = Store(create_database(GLSettings.db_uri))
        ret = config.is_cfg_valid(store)
        self.assertFalse(ret)
        store.close()

        migration.perform_data_update(self.db_file)

        store = Store(create_database(GLSettings.db_uri))
        prv = config.PrivateFactory(store)
        self.assertEqual(prv.get_val('version'), __version__)
        self.assertEqual(prv.get_val('xx_smtp_password'), self.dp)
        ret = config.is_cfg_valid(store)
        self.assertTrue(ret)
        store.close()

    def test_version_change_success(self):
        migration.perform_data_update(self.db_file)

        store = Store(create_database(GLSettings.db_uri))
        prv = config.PrivateFactory(store)
        self.assertEqual(prv.get_val('version'), __version__)
        store.close()

    def test_version_change_not_ok(self):
        # Set is_config_valid to false  during managed ver update
        config.is_cfg_valid = apply_gen(mod_bool)

        self.assertRaises(Exception, migration.perform_data_update, self.db_file)

        # Ensure the rollback has succeeded
        store = Store(create_database(GLSettings.db_uri))
        prv = config.PrivateFactory(store)
        self.assertEqual(prv.get_val('version'), self.dummy_ver)
        store.close()

    def test_ver_change_exception(self):
        # Explicity throw an exception in managed_ver_update via is_cfg_valid
        config.is_cfg_valid = apply_gen(throw_excep)

        self.assertRaises(IOError, migration.perform_data_update, self.db_file)

        store = Store(create_database(GLSettings.db_uri))
        prv = config.PrivateFactory(store)
        self.assertEqual(prv.get_val('version'), self.dummy_ver)
        store.close()

    def test_trim_value_to_range(self):
        store = Store(create_database(GLSettings.db_uri))

        nf = config.NodeFactory(store)
        fake_cfg = nf.get_cfg('wbtip_timetolive')

        self.assertRaises(errors.InvalidModelInput, fake_cfg.set_v, 3650)

        fake_cfg.value = {'v': 3650}
        store.commit()

        MigrationBase.trim_value_to_range(nf, 'wbtip_timetolive')
        self.assertEqual(nf.get_val('wbtip_timetolive'), 365*2)


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


class TestMigrationRegression(unittest.TestCase):
    def _initStartDB(self, target_ver):
        helpers.init_glsettings_for_unit_tests()

        GLSettings.db_path = os.path.join(GLSettings.ramdisk_path, 'db_test')
        os.mkdir(GLSettings.db_path)
        db_name = 'glbackend-%d.db' % target_ver
        db_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'db', 'populated', db_name)
        shutil.copyfile(db_path, os.path.join(GLSettings.db_path, db_name))

        self.db_file = os.path.join(GLSettings.db_path, db_name)
        GLSettings.db_uri = GLSettings.make_db_uri(self.db_file)

        self.store = Store(create_database(GLSettings.db_uri))

    def test_check_field_constraints(self):
        # This test case asserts that a migration from db ver 32 up to the latest
        # db with fields that fail the constraints still functions.
        self._initStartDB(32)

        field_dict = helpers.get_dummy_field()
        field_dict['instance'] = 'reference'
        field_dict['step_id'] = None
        field_dict['field_id'] = None

        db_create_field(self.store, field_dict, u'en')

        field_dict = helpers.get_dummy_field()
        field_dict['instance'] = 'instance'

        db_create_field(self.store, field_dict, u'en')

        field_dict = helpers.get_dummy_field()
        field_dict['instance'] = 'template'
        field_dict['step_id'] = None
        fld_grp_id = self.store.find(Field, Field.fieldgroup_id is not None)[0].fieldgroup_id
        field_dict['field_id'] = fld_grp_id

        db_create_field(self.store, field_dict, u'en')
        self.store.commit()

        ret = perform_system_update()
        shutil.rmtree(GLSettings.db_path)
        self.assertNotEqual(ret, -1)

    def test_check_unmodifiable_strings(self):
        # This test case asserts that data migration updates unmodifiable l10n strings
        self._initStartDB(34)

        notification_l10n = NotificationL10NFactory(self.store)

        t0 = notification_l10n.get_val('export_template', 'it')

        notification_l10n.set_val('export_template', 'it', '')

        t1 = notification_l10n.get_val('export_template', 'it')

        self.assertEqual(t1, '')

        self.store.commit()

        # place a dummy version in the current db
        store = Store(create_database(GLSettings.db_uri))
        prv = config.PrivateFactory(store)
        self.dummy_ver = '2.XX.XX'
        prv.set_val('version', self.dummy_ver)
        self.assertEqual(prv.get_val('version'), self.dummy_ver)
        store.commit()
        store.close()

        migration.perform_data_update(self.db_file)

        store = Store(create_database(GLSettings.db_uri))
        notification_l10n = NotificationL10NFactory(store)
        t2 = notification_l10n.get_val('export_template', 'it')
        self.assertEqual(t2, t0)
        store.commit()
        store.close()

        shutil.rmtree(GLSettings.db_path)
