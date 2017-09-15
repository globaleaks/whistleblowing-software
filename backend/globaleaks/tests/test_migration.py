"""
Test database migrations.

for each version one an empty and a populated db must be stored in directories:
 - db/empty
 - db/populated
"""

import os
import re
import shutil
from storm.locals import create_database, Store

from globaleaks import __version__, DATABASE_VERSION, FIRST_DATABASE_VERSION_SUPPORTED
from globaleaks.db import migration, update_db
from globaleaks.db.migrations import update_37
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import config
from globaleaks.models.config_desc import GLConfig
from globaleaks.models.l10n import EnabledLanguage, NotificationL10NFactory
from globaleaks.rest import errors
from globaleaks.settings import Settings
from globaleaks.tests import helpers, config as test_config
from twisted.trial import unittest


class TestMigrationRoutines(unittest.TestCase):
    def setUp(self):
        test_config.skipIf('migration')

    def _test(self, path, version):
        f = 'glbackend-%d.db' % version

        helpers.init_glsettings_for_unit_tests()
        Settings.db_path = os.path.join(Settings.ramdisk_path, 'db_test')
        self.start_db_file = os.path.abspath(os.path.join(Settings.db_path, 'glbackend-%d.db' % version))
        self.final_db_file = os.path.abspath(os.path.join(Settings.db_path, 'glbackend-%d.db' % DATABASE_VERSION))
        self.start_db_uri = Settings.make_db_uri(self.start_db_file)
        Settings.db_uri = Settings.make_db_uri(self.final_db_file)

        shutil.rmtree(Settings.db_path, True)
        os.mkdir(Settings.db_path)
        dbpath = os.path.join(path, f)
        dbfile = os.path.join(Settings.db_path, f)
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

        shutil.rmtree(Settings.db_path)
        self.assertNotEqual(ret, -1)

    def test_assert_complete(self):
        """
        This test asserts that every table defined in the schema is migrated

        Each CREATE TABLE statement is checked against a corresponding class name
        in the migration_table dict.
        """
        mig_class_names = {n.lower() for n in migration.migration_mapping.keys()}

        rel_path = os.path.join(os.path.abspath(__file__), '../../db/sqlite.sql')
        with open(os.path.abspath(rel_path), 'r') as f:
            s = f.read()
            raw_lst = re.findall(r'CREATE TABLE (\w+)', s)
            db_table_names = set()
            for name in raw_lst:
                db_table_names.add(name.replace('_', ''))

        diff = db_table_names - mig_class_names
        self.assertTrue(len(diff) == 0)

    def preconditions_34(self):
        store = Store(create_database(self.start_db_uri))
        notification_l10n = NotificationL10NFactory(store)
        notification_l10n.set_val(u'export_template', u'it', 'unmodifiable')
        x = notification_l10n.get_val(u'export_template', u'it')
        self.assertTrue(x, 'unmodifiable')
        store.commit()
        store.close()

    def postconditions_34(self):
        store = Store(create_database(Settings.db_uri))
        notification_l10n = NotificationL10NFactory(store)
        x = notification_l10n.get_val(u'export_template', u'it')
        self.assertNotEqual(x, 'unmodifiable')
        store.commit()
        store.close()

    def preconditions_36(self):
        update_37.TOR_DIR = Settings.db_path

        pk_path = os.path.join(update_37.TOR_DIR, 'private_key')
        hn_path = os.path.join(update_37.TOR_DIR, 'hostname')

        shutil.copy(os.path.join(helpers.DATA_DIR, 'tor/private_key'), pk_path)
        shutil.copy(os.path.join(helpers.DATA_DIR, 'tor/hostname'), hn_path)

    def postconditions_36(self):
        new_uri = Settings.make_db_uri(os.path.join(Settings.db_path, Settings.db_file_name))
        store = Store(create_database(new_uri))
        hs = config.NodeFactory(store, 1).get_val(u'onionservice')
        pk = config.PrivateFactory(store, 1).get_val(u'tor_onion_key')

        self.assertEqual('lftx7dbyvlc5txtl.onion', hs)
        with open(os.path.join(helpers.DATA_DIR, 'tor/ephemeral_service_key')) as f:
            saved_key = f.read().strip()
        self.assertEqual(saved_key, pk)
        store.close()


def test(path, version):
    return lambda self: self._test(path, version)


for directory in ['populated']:
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'db', directory)
    for i in range(FIRST_DATABASE_VERSION_SUPPORTED, DATABASE_VERSION):
        setattr(TestMigrationRoutines, "test_%s_db_migration_%d" % (directory, i), test(path, i))


class TestConfigUpdates(unittest.TestCase):
    def setUp(self):
        helpers.init_glsettings_for_unit_tests()

        Settings.db_path = os.path.join(Settings.ramdisk_path, 'db_test')
        shutil.rmtree(Settings.db_path, True)
        os.mkdir(Settings.db_path)
        db_name = 'glbackend-%d.db' % DATABASE_VERSION
        db_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'db', 'populated', db_name)
        shutil.copyfile(db_path, os.path.join(Settings.db_path, db_name))

        self.db_file = os.path.join(Settings.db_path, db_name)
        Settings.db_uri = Settings.make_db_uri(self.db_file)

        # place a dummy version in the current db
        store = Store(create_database(Settings.db_uri))
        prv = config.PrivateFactory(store)
        self.dummy_ver = '2.XX.XX'
        prv.set_val(u'version', self.dummy_ver)
        self.assertEqual(prv.get_val(u'version'), self.dummy_ver)
        store.commit()
        store.close()

        # backup various mocks that we will use
        self._bck_f = config.is_cfg_valid
        GLConfig['private']['xx_smtp_password'] = GLConfig['private'].pop('smtp_password')
        self.dp = u'yes_you_really_should_change_me'

    def tearDown(self):
        shutil.rmtree(Settings.db_path)
        GLConfig['private']['smtp_password'] = GLConfig['private'].pop('xx_smtp_password')
        config.is_cfg_valid = self._bck_f

    def test_migration_error_with_removed_language(self):
        store = Store(create_database(Settings.db_uri))
        zyx = EnabledLanguage(1, 'zyx')
        store.add(zyx)
        store.commit()
        store.close()

        self.assertRaises(Exception, migration.perform_data_update, self.db_file)

    def test_detect_and_fix_cfg_change(self):
        store = Store(create_database(Settings.db_uri))
        ret = config.is_cfg_valid(store)
        self.assertFalse(ret)
        store.close()

        migration.perform_data_update(self.db_file)

        store = Store(create_database(Settings.db_uri))
        prv = config.PrivateFactory(store)
        self.assertEqual(prv.get_val(u'version'), __version__)
        self.assertEqual(prv.get_val(u'xx_smtp_password'), self.dp)
        ret = config.is_cfg_valid(store)
        self.assertTrue(ret)
        store.close()

    def test_version_change_success(self):
        migration.perform_data_update(self.db_file)

        store = Store(create_database(Settings.db_uri))
        prv = config.PrivateFactory(store)
        self.assertEqual(prv.get_val(u'version'), __version__)
        store.close()

    def test_version_change_not_ok(self):
        # Set is_config_valid to false  during managed ver update
        config.is_cfg_valid = apply_gen(mod_bool)

        self.assertRaises(Exception, migration.perform_data_update, self.db_file)

        # Ensure the rollback has succeeded
        store = Store(create_database(Settings.db_uri))
        prv = config.PrivateFactory(store)
        self.assertEqual(prv.get_val(u'version'), self.dummy_ver)
        store.close()

    def test_ver_change_exception(self):
        # Explicity throw an exception in managed_ver_update via is_cfg_valid
        config.is_cfg_valid = apply_gen(throw_excep)

        self.assertRaises(IOError, migration.perform_data_update, self.db_file)

        store = Store(create_database(Settings.db_uri))
        prv = config.PrivateFactory(store)
        self.assertEqual(prv.get_val(u'version'), self.dummy_ver)
        store.close()

    def test_trim_value_to_range(self):
        store = Store(create_database(Settings.db_uri))

        nf = config.NodeFactory(store, 1)
        fake_cfg = nf.get_cfg(u'wbtip_timetolive')

        self.assertRaises(errors.InvalidModelInput, fake_cfg.set_v, 3650)

        fake_cfg.value = {'v': 3650}
        store.commit()

        MigrationBase.trim_value_to_range(nf, u'wbtip_timetolive')
        self.assertEqual(nf.get_val(u'wbtip_timetolive'), 365*2)


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
