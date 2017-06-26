# -*- coding: UTF-8

import os, re, shutil

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models.config import add_raw_config
from globaleaks.utils.utility import log


class MigrationScript(MigrationBase):
    def epilogue(self):
        """
        Imports the contents of the tor_hs directory into the config table

        NOTE the function does not delete the torhs dir, but instead leaves it
        on disk to ensure that the operator does not lose their HS key.
        """
        hostname, key = '', ''
        tor_dir = '/var/globaleaks/torhs'
        pk_path = os.path.join(tor_dir, 'private_key')
        hn_path = os.path.join(tor_dir, 'hostname')
        if os.path.exists(tor_dir) and os.path.exists(pk_path) and os.path.exists(hn_path):
            with open(hn_path, 'r') as f:
                hostname = f.read().strip()
               # TODO assert that the hostname corresponds with the key
                if not re.match(r'[A-Za-z0-9]{16}\.onion', hostname):
                    raise Exception('The hostname format does not match')

            with open(pk_path, 'r') as f:
               r = f.read()
               if not r.startswith('-----BEGIN RSA PRIVATE KEY-----\n'):
                   raise Exception('%s does not have the right format!')
               # Clean and convert the pem encoded key read into the format
               # expected by the ADD_ONION tor control protocol.
               # TODO assert the key passes deeper validation
               key = 'RSA1024:' + ''.join(r.strip().split('\n')[1:-1])

            shutil.rmtree(tor_dir)
        else:
           log.err('The structure of %s is incorrect. Cannot load onion service keys' % tor_dir)

        add_raw_config(self.store_new, u'node', u'onionservice', True, hostname)
        add_raw_config(self.store_new, u'private', u'tor_onion_key', True, key)

        self.entries_count['Config'] += 2
