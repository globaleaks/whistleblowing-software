"""
    GLBackend Database
    ******************

    :copyright: (c) 2012 by GlobaLeaks
    :license: see LICENSE for more details
"""
__all__ = ['models']

from twisted.python import log
from twisted.python.threadpool import ThreadPool
from twisted.internet.defer import inlineCallbacks, returnValue
from storm.twisted.transact import Transactor, transact
from storm.locals import *
from storm.uri import URI
from storm.databases.sqlite import SQLite

# File sqlite database
database_uri = 'sqlite:///globaleaks.db'
# In memory database
# database_uri = 'sqlite:'

database = SQLite(URI(database_uri))

threadpool = ThreadPool(0, 10)
threadpool.start()
transactor = Transactor(threadpool)

storepool = {}

def getStore():
    return Store(database)
"""
    import threading
    thread_id = threading.current_thread()
    if thread_id in storepool:
        return storepool[thread_id]
    else:
        storepool[thread_id] = Store(database)
        return storepool[thread_id]
"""

@inlineCallbacks
def find_one(*arg, **kw):
    store = getStore()
    results = yield transactor.run(store.find, *arg, **kw)
    the_one = results.one()
    store.close()
    returnValue(the_one)

@inlineCallbacks
def createTables():
    from globaleaks.db import models

    def create(query):
        store = getStore()
        store.execute(query)
        store.commit()

    for x in models.__all__:
        query = getattr(models.__getattribute__(x), 'createQuery')
        try:
            yield transactor.run(create, query)
        except:
            log.msg("Failing in creating table for %s. Maybe it already exists?" % x)


