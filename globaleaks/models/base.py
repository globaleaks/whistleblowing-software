import json

from twisted.internet.defer import returnValue

from storm.twisted.transact import transact
from storm.locals import *
import pickle

# under the voce of "needlessy overcomplications", Twister + Storm
# http://twistedmatrix.com/users/radix/storm-api/storm.store.ResultSet.html

from globaleaks.db import getStore, transactor, database
from globaleaks.db import tables

__all__ = ['InternalTip', 'Folder',
           'File', 'Tip','ReceiverTip',
           'Submission', 'Node', 'Receiver']

class TXModel(object):
    """
    This is the model to be subclassed for having the DB operations be done on
    storm ORM.

    The methods that should be run on the Storm ORM should be decorated with
    @transact. Be sure *not* to return any reference to Storm objects, these
    where retrieved in a different thread and cannot exit the matrix.

    When you decorate object methods with @transact be sure to also set the
    transactor attribute to that of a working transactor.
    """
    createQuery = ""
    transactor = transactor
    database = database

    def getStore(self):
        store = Store(self.database)
        return store

    @transact
    def createTable(self):
        store = self.getStore()
        createQuery = tables.generateCreateQuery(self)
        store.execute(createQuery)
        store.commit()
        store.close()

    @transact
    def save(self):
        store = self.getStore()
        store.add(self)
        store.commit()
        store.close()


"""
Triva, this file implement the 0.2 version of GlobaLeaks, then:
Enter the Ginger - http://www.youtube.com/watch?v=uUD9NBSJvqo
"""
