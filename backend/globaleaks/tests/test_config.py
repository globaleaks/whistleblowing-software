# -*- coding: utf-8 -*-
from globaleaks import LANGUAGES_SUPPORTED
from globaleaks.models import config
from globaleaks.models.config_desc import GLConfig
from globaleaks.models.l10n import NodeL10NFactory, EnabledLanguage, ConfigL10N
from globaleaks.orm import transact
from globaleaks.tests import helpers


class TestSystemConfigModels(helpers.TestGL):
    @transact
    def _test_config_import(self, store):
        c = store.find(config.Config, tid=1).count()

        stated_conf = reduce(lambda x,y: x+y, [len(v) for k, v in GLConfig.items()], 0)
        self.assertEqual(c, stated_conf)

    def test_config_import(self):
        return self._test_config_import()

    @transact
    def _test_valid_cfg(self, store):
        self.assertEqual(True, config.is_cfg_valid(store, 1))

    def test_valid_config(self):
        return self._test_valid_cfg()

    @transact
    def _test_missing_config(self, store):
        self.assertEqual(True, config.is_cfg_valid(store, 1))

        p = config.Config(1, 'private', 'smtp_password', 'XXXX')
        p.var_group = u'outside'
        store.add(p)

        self.assertEqual(False, config.is_cfg_valid(store, 1))

        node = config.NodeFactory(store, 1)
        c = node.get_cfg(u'hostname')
        store.remove(c)
        store.commit()

        self.assertEqual(False, node.db_corresponds())

        # Delete all of the vars in Private Factory
        prv = config.PrivateFactory(store, 1)

        store.execute('DELETE FROM config WHERE var_group = "private"')

        self.assertEqual(False, prv.db_corresponds())

        ntfn = config.NotificationFactory(store, 1)

        c = config.Config(1, 'notification', 'server', 'guarda.giochi.con.occhi')
        c.var_name = u'anextravar'
        store.add(c)

        self.assertEqual(False, ntfn.db_corresponds())

        config.update_defaults(store, 1)

        self.assertEqual(True, config.is_cfg_valid(store, 1))

    def test_missing_config(self):
        return self._test_missing_config()


class TestConfigL10N(helpers.TestGL):
    @transact
    def run_node_mgr(self, store):
        # Initialize the Node manager
        node_l10n = NodeL10NFactory(store)
        num_trans = len(NodeL10NFactory.localized_keys)

        # Make a query with the Node manager
        ret = node_l10n.retrieve_rows(u'en')

        self.assertTrue(len(ret) == num_trans)

    def test_config_l10n_init(self):
        return self.run_node_mgr()

    @transact
    def enable_langs(self, store):
        res = EnabledLanguage.list(store)

        self.assertTrue(u'en' in res)
        self.assertTrue(len(res) == len(LANGUAGES_SUPPORTED))

        c = store.find(ConfigL10N).count()
        self.assertTrue(1500 < c < 2300)

    def test_enabled_langs(self):
        return self.enable_langs()
