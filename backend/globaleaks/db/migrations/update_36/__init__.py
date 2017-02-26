# -*- coding: UTF-8
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import *
from globaleaks.models.config import Config, NodeFactory
from globaleaks.models.l10n import EnabledLanguage

from urlparse import urlparse


class MigrationScript(MigrationBase):
    def epilogue(self):
        def addConfig(store, group, name, customized, value):
            c = Config(migrate=True)
            c.var_group = group
            c.var_name =  name
            c.customixed = customized
            c.value = {'v': value}
            store.add(c)

        def delConfig(store, group, name):
            store.find(Config, Config.var_group == group, Config.var_name == name).remove()

        nnf = NodeFactory(self.store_new)
        url = nnf.get_val('public_site')
        o = urlparse(url)
        domain = o.netloc.split(':')[0]

        delConfig(self.store_new, u'node', u'public_site')
        addConfig(self.store_new, u'node', u'hostname', domain != '', domain)

        nnf = NodeFactory(self.store_new)
        url = nnf.get_val('hidden_service')
        o = urlparse(url)
        domain = o.netloc.split(':')[0]

        delConfig(self.store_new, u'node', u'hidden_service')
        addConfig(self.store_new, u'node', u'onionservice', domain != '', domain)

        self.store_new.commit()
