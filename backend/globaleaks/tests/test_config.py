# -*- coding: utf-8 -*-
from globaleaks import LANGUAGES_SUPPORTED
from globaleaks.models import config
from globaleaks.models.config_desc import ConfigDescriptor
from globaleaks.models.l10n import NodeL10NFactory, EnabledLanguage, ConfigL10N
from globaleaks.orm import transact
from globaleaks.tests import helpers


class TestSystemConfigModels(helpers.TestGL):
    @transact
    def _test_missing_config(self, store):
        node = config.NodeFactory(store, 1)
        c = node.get_cfg(u'hostname')
        store.remove(c)
        store.commit()

        self.assertEqual(False, node.db_corresponds())

        # Delete all of the vars in Private Factory
        prv = config.PrivateFactory(store, 1)

        store.execute('DELETE FROM config WHERE var_name = "server"')

        self.assertEqual(False, prv.db_corresponds())

        ntfn = config.NotificationFactory(store, 1)

        c = config.Config(1, 'server', 'guarda.giochi.con.occhi')
        c.var_name = u'anextravar'
        store.add(c)

        self.assertEqual(False, ntfn.db_corresponds())

        config.update_defaults(store, 1)

    def test_missing_config(self):
        return self._test_missing_config()
