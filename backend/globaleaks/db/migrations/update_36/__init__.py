# -*- coding: utf-8
from urllib.parse import urlparse  # pylint: disable=import-error

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models.properties import *


class MigrationScript(MigrationBase):
    def epilogue(self):
        config = self.model_to['Config']

        def add_raw_config(session, group, name, customized, value):
            c = config(migrate=True)
            c.var_group = group
            c.var_name = name
            c.customized = customized
            c.value = {'v': value}
            session.add(c)

        o = urlparse(self.session_new.query(config).filter(config.var_name == 'public_site').one().value['v'])
        domain = o.hostname if o.hostname is not None else ''

        self.session_new.query(config).filter(config.var_group == 'node', config.var_name == 'public_site').delete()

        add_raw_config(self.session_new, 'node', 'hostname', domain != '', domain)

        o = urlparse(self.session_new.query(config).filter(config.var_name == 'hidden_service').one().value['v'])
        domain = o.hostname if o.hostname is not None else ''

        self.session_new.query(config).filter(config.var_group == 'node', config.var_name == 'hidden_service').delete(synchronize_session=False)

        add_raw_config(self.session_new, 'node', 'onionservice', domain != '', domain)

        add_raw_config(self.session_new, 'node', 'reachable_via_web', False, False)
        self.entries_count['Config'] += 1

        self.session_new.commit()
