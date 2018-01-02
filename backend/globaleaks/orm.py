# -*- coding: utf-8
# orm: contains main hooks to storm ORM
# ******
import random
import time

from sqlite3.dbapi2 import OperationalError

from storm.database import create_database, Connection
from storm.databases import sqlite
from storm.store import Store

from twisted.internet import reactor
from twisted.internet.threads import deferToThreadPool


__DB_URI = 'sqlite:'
__THREAD_POOL = None


def make_db_uri(db_file):
    return 'sqlite:' + db_file + '?foreign_keys=ON'


def set_db_uri(db_uri):
    global __DB_URI
    __DB_URI = db_uri


def get_db_uri():
    global __DB_URI
    return __DB_URI


def get_store(db_uri=None):
    if db_uri is None:
        db_uri = get_db_uri()

    return Store(create_database(db_uri))


def set_thread_pool(thread_pool):
    global __THREAD_POOL
    __THREAD_POOL = thread_pool


def get_thread_pool():
    global __THREAD_POOL
    return __THREAD_POOL


class SQLiteConnectionMock(sqlite.SQLiteConnection):
    def raw_execute(self, statement, params=None, _end=False):
        if _end:
            self._in_transaction = False
        elif not self._in_transaction:
            # See story at the end to understand why we do BEGIN manually.
            self._in_transaction = True
            self._raw_connection.execute("BEGIN")

        try:
            return Connection.raw_execute(self, statement, params)
        except OperationalError as e:
            if str(e) == "database is locked" and _end:
                self._in_transaction = True
            raise


class SQLiteMock(sqlite.Database):
    connection_factory = SQLiteConnectionMock

    def __init__(self, uri):
        self._filename = uri.database or ":memory:"
        self._timeout = float(uri.options.get("timeout", 5))
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


sqlite.SQLite = SQLiteMock
sqlite.create_from_uri = SQLiteMock


class transact(object):
    """
    Class decorator for managing transactions.
    """
    def __init__(self, method):
        self.method = method
        self.instance = None

    def __get__(self, instance, owner):
        self.instance = instance
        return self

    def __call__(self, *args, **kwargs):
        return self.run(self._wrap, self.method, *args, **kwargs)

    def run(self, function, *args, **kwargs):
        return deferToThreadPool(reactor,
                                 get_thread_pool(),
                                 function,
                                 *args,
                                 **kwargs)

    def _wrap(self, function, *args, **kwargs):
        """
        Wrap provided function calling it inside a thread and
        passing the store to it.
        """
        store = get_store()

        try:
            while True:
                try:
                    if self.instance:
                        result = function(self.instance, store, *args, **kwargs)
                    else:
                        result = function(store, *args, **kwargs)

                    store.commit()
                except OperationalError as e:
                    store.rollback()
                    if str(e) != "database is locked":
                        raise
                    time.sleep(0.1)
                except Exception as e:
                    store.rollback()
                    raise
                else:
                    return result
        finally:
            store.reset()
            store.close()


class transact_sync(transact):
    def run(self, function, *args, **kwargs):
        return function(*args, **kwargs)
