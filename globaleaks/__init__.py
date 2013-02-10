# -*- encoding: utf-8 -*-
#
# In here we shall keep track of all variables and objects that should be
# instantiated only once and be common to pieces of GLBackend code.

__all__ = ['main']

from storm.twisted.transact import Transactor
from twisted.python.threadpool import ThreadPool

from globaleaks.config import config as cfg
from globaleaks.utils import log

from globaleaks.utils.singleton import Singleton

class Main(object):
    __metaclass__ = Singleton

    def __init__(self):
        log.debug("[D] %s %s " % (__file__, __name__), "Starting db_threadpool")
        self.db_threadpool = ThreadPool(0, cfg.advanced.db_thread_pool_size)
        self.db_threadpool.start()

        log.debug("[D] %s %s " % (__file__, __name__), "Starting scheduler_threadpool")
        self.scheduler_threadpool = ThreadPool(0, cfg.advanced.scheduler_thread_pool_size)
        self.scheduler_threadpool.start()

        self.transactor = Transactor(self.db_threadpool)
        self.transactor.retries = 0

main = Main()
