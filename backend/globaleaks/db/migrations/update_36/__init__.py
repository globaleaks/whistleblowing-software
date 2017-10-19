# -*- coding: utf-8

from urlparse import urlparse

from globaleaks import models
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models.config import NodeFactory


class MigrationScript(MigrationBase):
    def epilogue(self):
        def add_raw_config(store, group, name, customized, value):
            c = self.model_to['Config'](migrate=True)
            c.var_group = group
            c.var_name =  name
            c.customixed = customized
            c.value = {'v': value}
            store.add(c)

        o = urlparse(self.store_new.find(self.model_to['Config'], var_name=u'public_site').one().value['v'])
        domain = o.hostname if not o.hostname is None else ''

        models.db_delete(self.store_new, self.model_to['Config'], var_group=u'node', var_name=u'public_site')
        add_raw_config(self.store_new, u'node', u'hostname', domain != '', unicode(domain))

        o = urlparse(self.store_new.find(self.model_to['Config'], var_name=u'hidden_service').one().value['v'])
        domain = o.hostname if not o.hostname is None else ''

        models.db_delete(self.store_new, self.model_to['Config'], var_group=u'node', var_name=u'hidden_service')
        add_raw_config(self.store_new, u'node', u'onionservice', domain != '', unicode(domain))

        add_raw_config(self.store_new, u'node', u'reachable_via_web', False, False)
        self.entries_count['Config'] += 1

        self.store_new.commit()
