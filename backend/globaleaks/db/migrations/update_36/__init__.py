# -*- coding: UTF-8

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import *
from globaleaks.models.config import Config, NodeFactory, add_raw_config, del_config
from globaleaks.models.l10n import EnabledLanguage

from urlparse import urlparse

import os, re
from globaleaks.models.config import PrivateFactory, add_raw_config

class MigrationScript(MigrationBase):
    def migrate_hs_dir(self):
        '''Imports the contents of the tor_hs directory into the config table

        NOTE the function does not delete the torhs dir, but instead leaves it 
        on disk to ensure that the operator does not lose their HS key.
        '''
        priv_fact = PrivateFactory(self.store_new)

        tor_dir = '/var/globaleaks/torhs'
        pk_path = os.path.join(tor_dir, 'private_key')
        hn_path = os.path.join(tor_dir, 'hostname')
        if os.path.exists(pk_path) and os.path.exists(hn_path):
            with open(pk_path, 'r') as f:
               r = f.read()
               if not r.startswith('-----BEGIN RSA PRIVATE KEY-----\n'):
                   raise Exception('%s does not have the right format!')
               # Clean and convert the pem encoded key read into the format
               # expected by the ADD_ONION tor control protocol.
               # TODO assert the key passes deeper validation
               priv_key = 'RSA1024:' + ''.join(r.strip().split('\n')[1:-1])
            add_raw_config(self.store_new, u'private', u'tor_onion_priv_key', True, priv_key)

            with open(hn_path, 'r') as f:
                hostname = f.read().strip()
               # TODO assert that the hostname corresponds with the priv_key
                if not re.match(r'[A-Za-z0-9]{16}\.onion', hostname):
                    raise Exception('The hostname format does not match')
            add_raw_config(self.store_new, u'private', u'tor_onion_hostname', True, hostname)
        else:
           raise Exception('The structure of %s is incorrect. Cannot load onion service keys' % tor_dir)

        self.entries_count['Config'] += 2

    def epilogue(self):
        nf = NodeFactory(self.store_new)
        url = nf.get_val('public_site')
        o = urlparse(url)
        domain = o.hostname if not o.hostname is None else ''

        del_config(self.store_new, u'node', u'public_site')
        add_raw_config(self.store_new, u'node', u'hostname', domain != '', unicode(domain))

        url = nf.get_val('hidden_service')
        o = urlparse(url)
        domain = o.hostname if not o.hostname is None else ''

        del_config(self.store_new, u'node', u'hidden_service')
        add_raw_config(self.store_new, u'node', u'onionservice', domain != '', unicode(domain))

        add_raw_config(self.store_new, u'node', u'reachable_via_web', False, False)
        self.entries_count['Config'] += 1

        self.migrate_hs_dir()

        self.store_new.commit()
