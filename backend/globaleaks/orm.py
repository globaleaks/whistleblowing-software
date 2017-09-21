# -*- coding: UTF-8
# orm: contains main hooks to storm ORM
# ******
import sys
import threading
from datetime import datetime
from storm import tracer
from storm.database import create_database
import storm.databases.sqlite
from storm.databases import sqlite
from storm.store import Store

from globaleaks.settings import GLSettings
from globaleaks.utils.mailutils import schedule_exception_email
from globaleaks.utils.utility import log, timedelta_to_milliseconds
from twisted.internet import reactor
from twisted.internet.threads import deferToThreadPool


def get_store():
    return Store(create_database(GLSettings.db_uri))


class SQLite(sqlite.Database):
    connection_factory = sqlite.SQLiteConnection

    def __init__(self, uri):
        self._filename = uri.database or ":memory:"
        self._timeout = float(uri.options.get("timeout", 30))
        self._foreign_keys = uri.options.get("foreign_keys")

    def raw_connect(self):
        raw_connection = sqlite.sqlite.connect(self._filename,
                                               timeout=self._timeout,
                                               isolation_level=None)

        if self._foreign_keys is not None:
            raw_connection.execute("PRAGMA foreign_keys = %s" %
                                   (self._foreign_keys,))

        raw_connection.execute("PRAGMA secure_delete = ON")

        return raw_connection


storm.databases.sqlite.SQLite = SQLite
storm.databases.sqlite.create_from_uri = SQLite
transact_lock = threading.Lock()


class transact(object):
    """
    Class decorator for managing transactions.
    Because Storm sucks.
    """
    timelimit = 30000

    def __init__(self, method):
        self.method = method
        self.instance = None
        self.debug = GLSettings.orm_debug

        tracer.debug(self.debug, sys.stdout)

    def __get__(self, instance, owner):
        self.instance = instance
        return self

    def __call__(self, *args, **kwargs):
        return self.run(self._wrap, self.method, *args, **kwargs)

    def run(self, function, *args, **kwargs):
        return deferToThreadPool(reactor,
                                 GLSettings.orm_tp,
                                 function,
                                 *args,
                                 **kwargs)

    def _wrap(self, function, *args, **kwargs):
        """
        Wrap provided function calling it inside a thread and
        passing the store to it.
        """
        with transact_lock: # pylint: disable=not-context-manager
            start_time = datetime.now()
            store = get_store()

            try:
                if self.instance:
                    result = function(self.instance, store, *args, **kwargs)
                else:
                    result = function(store, *args, **kwargs)

                store.commit()
            except:
                store.rollback()
                raise
            else:
                return result
            finally:
                store.reset()
                store.close()

                duration = timedelta_to_milliseconds(datetime.now() - start_time)
                err_tup = "Query [%s] executed in %.1fms", self.method.__name__, duration
                if duration > self.timelimit:
                    log.err(*err_tup)
                    schedule_exception_email(*err_tup)
                else:
                    log.debug(*err_tup)


class transact_sync(transact):
    def run(self, function, *args, **kwargs):
        return function(*args, **kwargs)
