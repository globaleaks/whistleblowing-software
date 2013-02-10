# -*- coding: UTF-8
#   config
#   ******
#
# Configuration file do not contain GlobaLeaks Node information, like in the 0.1
# because all those infos are stored in the databased.
# Config contains some system variables usable for debug, integration with APAF and
# nothing in the common concern af a GlobaLeaks Node Admin


import os, sys

import transaction
from twisted.python import log
from cyclone.util import ObjectDict as OD
from storm.zope.zstorm import ZStorm
from storm.tracer import debug

from globaleaks.utils.singleton import Singleton

class ConfigError(Exception):
    pass

def get_root_path():
    this_directory = os.path.dirname(__file__)
    root = os.path.join(this_directory, '..')
    root = os.path.abspath(root)
    return root

def get_install_path():
    return os.path.abspath(os.path.join(get_root_path(), '..'))

def get_glclient_path():
    path = '/tmp'

    # XXX move all these variables to a config file
    glclient_path = os.path.join(get_install_path(), 'GLClient', 'app')
    path = os.path.abspath(glclient_path)
    if not os.path.isdir(path):
        raise ConfigError("GLClient not found at the %s path" % glclient_path)

    return path

def get_db_file(filename=None):
    root = get_root_path()
    db_dir = os.path.join(root, '_gldata')
    if not os.path.isdir(db_dir):
        os.mkdir(db_dir)
    db_file = os.path.join(db_dir, filename)
    return db_file

class Config(object):
    def __init__(self, database_file=None, store='main_store'):
        self.debug = OD()

        # 'testing' is present, GUS are incremental
        cmdline_opt = sys.argv
        if 'testing' in cmdline_opt:
            self.debug.testing = True
        else:
            self.debug.testing = False

        # 'db' is present, Storm debug enabed
        if 'db' in cmdline_opt:
            debug(True, sys.stdout)
        else:
            debug(False, sys.stdout)

        # 'verbose' is present, show JSON receiver messages
        if 'verbose' in cmdline_opt:
            self.debug.verbose = True
        else:
            self.debug.verbose = False

        self.advanced = OD()
        self.advanced.debug = True

        self.main = OD()
        self.main.glclient_path = get_glclient_path()

        self.sessions = dict()

        if self.advanced.debug:
            log.msg("Serving GLClient from %s" % self.main.glclient_path)

        # This is the zstorm store used for transactions
        if database_file:
            self.main.database_uri = 'sqlite:'+database_file
        else:
            self.main.database_uri = 'sqlite:'+get_db_file('glbackend.db')

        self.main.zstorm = ZStorm()
        self.main.zstorm.set_default_uri(store, self.main.database_uri)
        self.store = store

        self.advanced.db_thread_pool_size = 1
        self.advanced.scheduler_thread_pool_size = 10

        self.advanced.data_dir = os.path.join(get_root_path(), '_gldata')
        self.advanced.submissions_dir = os.path.join(self.advanced.data_dir, 'submissions')
        self.advanced.delivery_dir = os.path.join(self.advanced.data_dir, 'delivery')

config = Config()
