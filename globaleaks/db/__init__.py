"""
    GLBackend Database
    ******************

    :copyright: (c) 2012 by GlobaLeaks
    :license: see LICENSE for more details
"""
__all__ = ['models']

from twisted.python import log
from twisted.python.threadpool import ThreadPool
from twisted.internet.defer import inlineCallbacks
from storm.twisted.transact import Transactor, transact
from storm.locals import *

dbtype = "sqlite"

if dbtype == "sqlite":
    from storm.uri import URI
    from storm.databases.sqlite import SQLite
    database = SQLite(URI('sqlite:///test.db'))

threadpool = ThreadPool(0, 10)
threadpool.start()
transactor = Transactor(threadpool)

@inlineCallbacks
def create_tables():
    from globaleaks.db import models
    def create(query):
        store = Store(database)
        store.execute(query)
        store.commit()

    for x in models.__all__:
        query = getattr(models.__getattribute__(x), 'create_query')
        try:
            yield transactor.run(create, query)
        except:
            log.msg("Failing in creating table for %s. Maybe it already exists?" % x)

