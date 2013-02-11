# -*- coding: UTF-8
#
#   models/base
#   *******
#
# TXModel class is the superclass of all the Storm operation in models/*.py

import transaction
from storm.locals import Store, Storm
from storm.twisted.transact import transact

from globaleaks import settings
from globaleaks.utils import log

__all__ = ['TXModel' ]

class TXModel(Storm):
    """
    This is the model to be subclassed for having the DB operations be done on
    storm ORM.

    The methods that should be run on the Storm ORM should be decorated with
    @transact. Be sure *not* to return any reference to Storm objects, these
    where retrieved in a different thread and cannot exit the matrix.

    When you decorate object methods with @transact be sure to also set the
    transactor attribute to that of a working transactor.

    An example of what is the right way to do it (taken from
    models/submission.py):
        store = self.getStore()
        [...]
        s = store.find(Submission,
                    Submission.submission_id==submission_id).one()
        [...]
        ... Do other stuff with s ...
    """
    log.debug("[D] %s %s " % (__file__, __name__), "Class TXModel")

    transactor = settings.main.transactor

    createQuery = ""

    # class variable keeping track in incremental mode to DB I/O access
    sequencial_dbop = 0

    # remind, I've tried to make a wrapper around the store.close()
    # in order to help debug. no, it can't work:
    #
    #   sqlite3.ProgrammingError: SQLite objects created in a thread can only be used
    #   in that same thread.The object was created in thread id 140400639661824
    #   and this is thread id 140400631269120
    #
    # and is extremely difficult debug this crap, without assistance, the
    # 'database is locked' should happen also when a transact function has a typo
    # inside, and silently would simply stay freezed, keeping DB locked.

    def __init__(self, theStore):
        self.store = theStore

# Triva, this file implement the 0.2 version of GlobaLeaks, then:
# Enter the Ginger - http://www.youtube.com/watch?v=uUD9NBSJvqo
