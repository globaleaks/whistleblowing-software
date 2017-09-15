# -*- coding: utf-8

from urlparse import urlparse

from globaleaks import models
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models.config import Config, NodeFactory, add_raw_config


class MigrationScript(MigrationBase):
    def epilogue(self):
        nf = NodeFactory(self.store_new, 1)
        url = nf.get_val(u'public_site')
        o = urlparse(url)
        domain = o.hostname if not o.hostname is None else ''

        models.db_delete(self.store_new, Config, var_group=u'node', var_name=u'public_site')
        add_raw_config(self.store_new, u'node', u'hostname', domain != '', unicode(domain))

        url = nf.get_val(u'hidden_service')
        o = urlparse(url)
        domain = o.hostname if not o.hostname is None else ''

        models.db_delete(self.store_new, Config, var_group=u'node', var_name=u'hidden_service')
        add_raw_config(self.store_new, u'node', u'onionservice', domain != '', unicode(domain))

        add_raw_config(self.store_new, u'node', u'reachable_via_web', False, False)
        self.entries_count['Config'] += 1

        self.store_new.commit()
