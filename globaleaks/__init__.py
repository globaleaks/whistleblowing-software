# -*- encoding: utf-8 -*-
#
# In here we shall keep track of all variables and objects that should be
# instantiated only once and be common to pieces of GLBackend code.

__all__ = ['database', 'db_threadpool', 'scheduler_threadpool', 'work_manager']

from storm.uri import URI
from storm.twisted.transact import Transactor

from twisted.python.threadpool import ThreadPool

from globaleaks import config
from globaleaks.utils import log

log.debug("[D] %s %s " % (__file__, __name__), "Starting db_threadpool")
db_threadpool = ThreadPool(0, config.advanced.db_thread_pool_size)
db_threadpool.start()
transactor = Transactor(db_threadpool)

log.debug("[D] %s %s " % (__file__, __name__), "Starting scheduler_threadpool")
scheduler_threadpool = ThreadPool(0, config.advanced.scheduler_thread_pool_size)
scheduler_threadpool.start()


