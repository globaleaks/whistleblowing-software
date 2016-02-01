# -*- coding: UTF-8
# orm: contains main hooks to storm ORM
# ******
import sys
import transaction

from cyclone.web import HTTPError

from storm import exceptions, tracer
from storm.databases.sqlite import sqlite
from storm.zope.zstorm import ZStorm

from twisted.internet import reactor
from twisted.internet.defer import succeed
from twisted.internet.threads import deferToThreadPool

from globaleaks.rest.errors import DatabaseIntegrityError
from globaleaks.settings import GLSettings


# XXX. MONKEYPATCH TO SUPPORT STORM 0.19
import storm.databases.sqlite


class SQLite(storm.databases.sqlite.Database):
    connection_factory = storm.databases.sqlite.SQLiteConnection

    def __init__(self, uri):
        if sqlite is storm.databases.sqlite.dummy:
            raise storm.databases.sqlite.DatabaseModuleError("'pysqlite2' module not found")
        self._filename = uri.database or ":memory:"
        self._timeout = float(uri.options.get("timeout", 5))
        self._synchronous = uri.options.get("synchronous")
        self._journal_mode = uri.options.get("journal_mode")
        self._foreign_keys = uri.options.get("foreign_keys")

    def raw_connect(self):
        # See the story at the end to understand why we set isolation_level.
        raw_connection = sqlite.connect(self._filename, timeout=self._timeout,
                                        isolation_level=None)
        if self._synchronous is not None:
            raw_connection.execute("PRAGMA synchronous = %s" %
                                   (self._synchronous,))

        if self._journal_mode is not None:
            raw_connection.execute("PRAGMA journal_mode = %s" %
                                   (self._journal_mode,))

        if self._foreign_keys is not None:
            raw_connection.execute("PRAGMA foreign_keys = %s" %
                                   (self._foreign_keys,))

        return raw_connection

storm.databases.sqlite.SQLite = SQLite
storm.databases.sqlite.create_from_uri = SQLite
# XXX. END MONKEYPATCH


class transact(object):
    """
    Class decorator for managing transactions.
    Because Storm sucks.
    """
    readonly = False

    def __init__(self, method):
        self.store = None
        self.method = method
        self.instance = None
        self.debug = GLSettings.orm_debug

        if self.debug:
            tracer.debug(self.debug, sys.stdout)

    def __get__(self, instance, owner):
        self.instance = instance
        return self

    def __call__(self, *args, **kwargs):
        return self.run(self._wrap, self.method, *args, **kwargs)

    @staticmethod
    def run(function, *args, **kwargs):
        """
        Defer provided function to thread
        """
        return deferToThreadPool(reactor, GLSettings.orm_tp,
                                 function, *args, **kwargs)

    @staticmethod
    def get_store():
        """
        Returns a reference to Storm Store
        """
        zstorm = ZStorm()
        zstorm.set_default_uri(GLSettings.store_name, GLSettings.db_uri)

        return zstorm.get(GLSettings.store_name)

    def _wrap(self, function, *args, **kwargs):
        """
        Wrap provided function calling it inside a thread and
        passing the store to it.
        """
        self.store = self.get_store()

        try:
            if self.instance:
                result = function(self.instance, self.store, *args, **kwargs)
            else:
                result = function(self.store, *args, **kwargs)

            if not self.readonly:
                self.store.commit()
            else:
                self.store.flush()
                self.store.invalidate()

        except exceptions.DisconnectionError as e:
            transaction.abort()
            result = None
        except exceptions.IntegrityError as e:
            transaction.abort()
            raise DatabaseIntegrityError(str(e))
        except Exception as e:
            transaction.abort()
            raise
        finally:
            self.store.close()

        return result


class transact_ro(transact):
    readonly = True
