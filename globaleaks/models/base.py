# under the voce of "needlessy overcomplications", Twister + Storm
# http://twistedmatrix.com/users/radix/storm-api/storm.store.ResultSet.html

from storm.locals import Store
from storm.twisted.transact import transact

from globaleaks.db import transactor, database
from globaleaks.db import tables
from globaleaks.utils import log

__all__ = ['TXModel', 'ModelError']

class TXModel(object):
    """
    This is the model to be subclassed for having the DB operations be done on
    storm ORM.

    The methods that should be run on the Storm ORM should be decorated with
    @transact. Be sure *not* to return any reference to Storm objects, these
    where retrieved in a different thread and cannot exit the matrix.

    When you decorate object methods with @transact be sure to also set the
    transactor attribute to that of a working transactor.

    It is very important that all exceptions that happen when a the store is
    open are trapped and the store is rolled back and closed. If this is not
    done we will start having database locking issues and we will start to
    enter a valley of pain.

    An example of what is the right way to do it (taken from
    models/submission.py):
        store = self.getStore()
        [...]
        s = store.find(Submission,
                    Submission.submission_id==submission_id).one()
        [...]
        if not s:
            store.rollback()
            store.close()
            raise SubmissionNotFoundError

        ... Do other stuff with s ...

    Where SubmissionNotFoundError is a subclass of ModelError.

    This exception should then be trapped in the handler and set the error
    status code and write the error out.
    """
    log.debug("[D] %s %s " % (__file__, __name__), "Class TXModel")
    createQuery = ""
    transactor = transactor
    database = database

    def getStore(self):
        log.debug("[D] %s %s " % (__file__, __name__), "Class TXModel", "getStore")
        store = Store(self.database)
        return store

    @transact
    def createTable(self):
        log.debug("[D] %s %s " % (__file__, __name__), "Class TXModel", "createTable")
        store = self.getStore()
        createQuery = tables.generateCreateQuery(self)
        store.execute(createQuery)
        store.commit()
        store.close()

    @transact
    def save(self):
        log.debug("[D] %s %s " % (__file__, __name__), "Class TXModel", "save")
        store = self.getStore()
        store.add(self)
        store.commit()
        store.close()

class ModelError(Exception):
    log.debug("[D] %s %s " % (__file__, __name__), "Class ModelError")
    pass

"""
Triva, this file implement the 0.2 version of GlobaLeaks, then:
Enter the Ginger - http://www.youtube.com/watch?v=uUD9NBSJvqo
"""
