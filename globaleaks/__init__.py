# -*- encoding: utf-8 -*-
#
# :authors: Arturo Filastò
# :licence: see LICENSE

"""
In here we shall keep track of all variables and objects that should be
instantiated only once and be common to pieces of GLBackend code.
"""
from storm.uri import URI
from storm.twisted.transact import Transactor
from storm.databases.sqlite import SQLite

from twisted.python.threadpool import ThreadPool

from globaleaks.scheduler import manager
from globaleaks import config

database = SQLite(URI(config.main.database_uri))
db_threadpool = ThreadPool(0, config.advanced.db_thread_pool_size)
db_threadpool.start()
transactor = Transactor(db_threadpool)

scheduler_threadpool = ThreadPool(0,
        config.advanced.scheduler_thread_pool_size)
scheduler_threadpool.start()

work_manager = manager.DBWorkManager()
work_manager.restoreState()

