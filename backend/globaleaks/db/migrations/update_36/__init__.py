# -*- coding: utf-8
from urlparse import urlparse

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models.properties import *


class MigrationScript(MigrationBase):
    def epilogue(self):
        config = self.model_to['Config']

        def add_raw_config(session, group, name, customized, value):
            c = config(migrate=True)
            c.var_group = group
            c.var_name =  name
            c.customixed = customized
            c.value = {'v': value}
            session.add(c)

        o = urlparse(self.session_new.query(config).filter(config.var_name == u'public_site').one().value['v'])
        domain = o.hostname if not o.hostname is None else ''

        self.session_new.query(config).filter(config.var_group == u'node', config.var_name == u'public_site').delete()

        add_raw_config(self.session_new, u'node', u'hostname', domain != '', unicode(domain))

        o = urlparse(self.session_new.query(config).filter(config.var_name == u'hidden_service').one().value['v'])
        domain = o.hostname if not o.hostname is None else ''

        self.session_new.query(config).filter(config.var_group == u'node', config.var_name == u'hidden_service').delete(synchronize_session='fetch')

        add_raw_config(self.session_new, u'node', u'onionservice', domain != '', unicode(domain))

        add_raw_config(self.session_new, u'node', u'reachable_via_web', False, False)
        self.entries_count['Config'] += 1

        self.session_new.commit()
