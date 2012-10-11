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

class StorePool(object):
    def __init__(self, database=database):
        self.database = database
        self._stores = []
        self._stores_created = 0
        self._pending_get = []
        self._store_refs = []

def getStore():
    """
    if name in storepool:
        return storepool[name]
    else:
        storepool[name] = Store(database)
        return storepool[name]
    """
    s = Store(database)
    return s

@inlineCallbacks
def find_one(*arg, **kw):
    store = getStore()
    print "Find one!"
    results = yield transactor.run(store.find, *arg, **kw)
    the_one = results.one()
    print the_one
    store.commit()
    store.close()
    print the_one
    returnValue(the_one)

@inlineCallbacks
def remove(obj, *arg, **kw):
    print "Removing!"
    store = getStore()
    #Store.of(obj)
    results = yield transactor.run(store.remove, obj)
    store.commit()
    store.close()

@inlineCallbacks
def createTables():
    from globaleaks.db import models

    def create(query):
        store = getStore()
        store.execute(query)
        store.commit()
        store.close()

    for x in models.__all__:
        query = getattr(models.__getattribute__(x), 'createQuery')
        try:
            yield transactor.run(create, query)
        except:
            log.msg("Failing in creating table for %s. Maybe it already exists?" % x)

