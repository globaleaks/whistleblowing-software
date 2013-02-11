# -*- coding: UTF-8
#   config
#   ******
#
# Configuration file do not contain GlobaLeaks Node information, like in the 0.1
# because all those infos are stored in the databased.
# Config contains some system variables usable for debug, integration with APAF and
# nothing in the common concern af a GlobaLeaks Node Admin


import os
import os.path
import sys

import transaction
from twisted.python import log
from twisted.python.threadpool import ThreadPool
from cyclone.util import ObjectDict as OD
from storm.zope.zstorm import ZStorm
from storm.tracer import debug
from storm.twisted.transact import Transactor
from globaleaks.utils.singleton import Singleton
from globaleaks.utils.singleton import Singleton


root_path = os.path.join(os.path.dirname(__file__), '..')
install_path = os.path.abspath(os.path.join(root_path, '..'))
glclient_path = os.path.join(install_path, 'GLClient', 'app')
gldata_path = os.path.join(root_path, '_gldata')
db_file = 'sqlite:' + os.path.join(gldata_path, 'glbackend.db')
store_name = 'main_store'

if not os.path.exists(gldata_path):
        os.mkdir(gldata_path)

assert all(os.path.exists(path) for path in
           (root_path, install_path, glclient_path, gldata_path))

def get_store():
    zstorm = ZStorm()
    zstorm.set_default_uri(store_name, db_file)
    return zstorm.get(store_name)

class Config(object):
    def __init__(self):
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
        self.main.glclient_path = glclient_path

        self.sessions = dict()

        if self.advanced.debug:
            log.msg("Serving GLClient from %s" % self.main.glclient_path)

        # This is the zstorm store used for transactions
        self.main.database_uri = db_file

        self.main.zstorm = ZStorm()
        self.main.zstorm.set_default_uri(store_name, db_file)

        self.advanced.db_thread_pool_size = 1
        self.advanced.scheduler_thread_pool_size = 10

        self.advanced.data_dir = gldata_path
        self.advanced.submissions_dir = os.path.join(self.advanced.data_dir, 'submissions')
        self.advanced.delivery_dir = os.path.join(self.advanced.data_dir, 'delivery')

        log.msg("[D] %s %s " % (__file__, __name__), "Starting db_threadpool")
        self.main.db_threadpool = ThreadPool(0, self.advanced.db_thread_pool_size)
        self.main.db_threadpool.start()

        log.msg("[D] %s %s " % (__file__, __name__), "Starting scheduler_threadpool")
        self.main.scheduler_threadpool = ThreadPool(0, self.advanced.scheduler_thread_pool_size)
        self.main.scheduler_threadpool.start()

        self.main.transactor = Transactor(self.main.db_threadpool)
        self.main.transactor.retries = 0

    @property
    def store(self): return get_store()

config = Config()

