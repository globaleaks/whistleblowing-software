# -*- coding: utf-8 -*-
from globaleaks import models, LANGUAGES_SUPPORTED
from globaleaks.models import config
from globaleaks.models.config_desc import GLConfig
from globaleaks.models.l10n import NodeL10NFactory, EnabledLanguage, ConfigL10N
from globaleaks.orm import transact
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestSystemConfigModels(helpers.TestGL):
    @inlineCallbacks
    def test_config_import(self):
        yield self._test_config_import()

    @transact
    def _test_config_import(self, store):
        c = store.find(config.Config).count()

        stated_conf = reduce(lambda x,y: x+y, [len(v) for k, v in GLConfig.items()], 0)
        self.assertEqual(c, stated_conf)

    @inlineCallbacks
    def test_valid_config(self):
        yield self._test_valid_cfg()

    @transact
    def _test_valid_cfg(self, store):
        self.assertEqual(True, config.is_cfg_valid(store))

    @inlineCallbacks
    def test_missing_config(self):
        yield self._test_missing_config()

    @transact
    def _test_missing_config(self, store):
        self.assertEqual(True, config.is_cfg_valid(store))

        p = config.Config('private', 'smtp_password', 'XXXX')
        p.var_group = u'outside'
        store.add(p)

        self.assertEqual(False, config.is_cfg_valid(store))

        node = config.NodeFactory(store)
        c = node.get_cfg('hostname')
        store.remove(c)
        store.commit()

        self.assertEqual(False, node.db_corresponds())

        # Delete all of the vars in Private Factory
        prv = config.PrivateFactory(store)

        store.execute('DELETE FROM config WHERE var_group = "private"')

        self.assertEqual(False, prv.db_corresponds())

        ntfn = config.NotificationFactory(store)

        c = config.Config('notification', 'server', 'guarda.giochi.con.occhi')
        c.var_name = u'anextravar'
        store.add(c)

        self.assertEqual(False, ntfn.db_corresponds())

        config.update_defaults(store)

        self.assertEqual(True, config.is_cfg_valid(store))


class TestConfigL10N(helpers.TestGL):
    @inlineCallbacks
    def test_config_l10n_init(self):
        yield self.run_node_mgr()

    @transact
    def run_node_mgr(self, store):
        # Initialize the Node manager
        node_l10n = NodeL10NFactory(store)
        num_trans = len(NodeL10NFactory.localized_keys)

        # Make a query with the Node manager
        ret = node_l10n.retrieve_rows('en')

        self.assertTrue(len(ret) == num_trans)

    @transact
    def enable_langs(self, store):
        res = EnabledLanguage.list(store)

        self.assertTrue(u'en' in res)
        self.assertTrue(len(res) == len(LANGUAGES_SUPPORTED))

        c = store.find(ConfigL10N).count()
        self.assertTrue(1500 < c < 2300)

    @inlineCallbacks
    def test_enabled_langs(self):
        yield self.enable_langs()
