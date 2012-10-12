"""
    GLBackend Database
    ******************

    :copyright: (c) 2012 by GlobaLeaks
    :license: see LICENSE for more details
"""
__all__ = ['models']

from twisted.python import log
from twisted.python.threadpool import ThreadPool
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
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

def getStore():
    s = Store(database)
    return s

@inlineCallbacks
def createTables():
    from globaleaks.db import models
    d = Deferred()
    def create(query):
        store = getStore()
        store.execute(query)
        store.commit()
        store.close()

    for x in models.__all__:
        query = getattr(models.__getattribute__(x), 'createQuery')
        try:
            yield transactor.run(create, query)
            pass
        except:
            log.msg("Failing in creating table for %s. Maybe it already exists?" % x)

    r = models.Receiver()
    receiver_dicts = yield r.receiver_dicts()

    if not receiver_dicts:
        print "Creating dummy receiver tables"
        receiver_dicts = yield r.create_dummy_receivers()

    print "These are the the installed receivers:"
    for receiver in receiver_dicts:
        print "-----------------"
        print receiver
        print "-----------------"

