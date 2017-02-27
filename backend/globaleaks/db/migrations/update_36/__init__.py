# -*- coding: UTF-8

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import *
from globaleaks.models.config import Config, NodeFactory, addUnicodeConfig, delConfig
from globaleaks.models.l10n import EnabledLanguage

from urlparse import urlparse


class MigrationScript(MigrationBase):
    def epilogue(self):
        nnf = NodeFactory(self.store_new)
        url = nnf.get_val('public_site')
        o = urlparse(url)
        domain = o.netloc.split(':')[0]

        delConfig(self.store_new, u'node', u'public_site')
        addUnicodeConfig(self.store_new, u'node', u'hostname', domain != '', unicode(domain))

        nnf = NodeFactory(self.store_new)
        url = nnf.get_val('hidden_service')
        o = urlparse(url)
        domain = o.netloc.split(':')[0]

        delConfig(self.store_new, u'node', u'hidden_service')
        addUnicodeConfig(self.store_new, u'node', u'onionservice', domain != '', unicode(domain))

        self.store_new.commit()
