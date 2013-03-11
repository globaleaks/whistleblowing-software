# -*- coding: UTF-8
#   config
#   ******
#
# Configuration file do not contain GlobaLeaks Node information, like in the 0.1
# because all those infos are stored in the databased.
# Config contains some system variables usable for debug, integration with APAF and
# nothing in the common concern af a GlobaLeaks Node Admin


import os
import sys
import traceback
import logging
import transaction

from optparse import OptionParser
from twisted.python import log
from twisted.python.threadpool import ThreadPool
from twisted.internet import reactor
from storm import exceptions
from twisted.internet.threads import deferToThreadPool
from cyclone.web import HTTPError
from storm.zope.zstorm import ZStorm
from storm import tracer


verbosity_dict = {
    'INFO' : logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
    'DEBUG': logging.DEBUG
}

class GLSettingsClass:

    def __init__(self):

        # command line parsing utils
        self.parser = OptionParser()
        self.cmdline_options = None

        # threads sizes
        self.db_thread_pool_size = 1

        # files and path
        self.store_name = 'main_store'
        self.root_path = os.path.join(os.path.dirname(__file__), '..')
        self.install_path = os.path.abspath(os.path.join(self.root_path, '..'))
        self.glclient_path = os.path.join(self.install_path, 'GLClient', 'app')
        self.gldata_path = os.path.join(self.root_path, '_gldata')
        self.db_file = 'sqlite:' + os.path.join(self.gldata_path, 'glbackend.db')
        self.create_db_file = os.path.join(self.root_path, 'globaleaks', 'db', 'sqlite.sql')
        self.static_path = os.path.join(self.root_path, '_static')
        self.logfile = os.path.join(self.gldata_path, 'glbackend.log')
        self.receipt_regexp = r'[A-Z]{4}\+[0-9]{5}'

        # List of plugins available in the software
        self.notification_plugins = [
            'MailNotification',
            ]

        # Debug Defaults
        self.db_debug = True
        self.cyclone_debug = -1
        self.loglevel = logging.DEBUG

        # Session tracking, in the singleton classes
        self.sessions = dict()

        # value limits in the database
        self.name_limit = 128
        self.description_limit = 1024
        self.generic_limit = 2048


    def load_cmdline_options(self):
        """
        This function is called by runner.py and operate in cmdline_options,
        interpreted and filled in bin/startglobaleaks script.

        happen in startglobaleaks before the sys.argv is modified
        """
        assert self.cmdline_options is not None

        self.db_debug = self.cmdline_options.storm

        self.loglevel = verbosity_dict[self.cmdline_options.loglevel]
        self.bind_port = self.cmdline_options.port

        # If user has requested this option, initialize a counter to
        # record the requests sequence, and setup the logs path
        if self.cmdline_options.io >= 0:
            self.cyclone_debug = self.cmdline_options.io
            self.cyclone_debug_counter = 0
            self.cyclone_io_path = os.path.join(self.gldata_path, "cyclone_debug")


    def consistency_check(self):

        if not os.path.exists(self.gldata_path):
            os.mkdir(self.gldata_path)

        if not os.path.exists(self.static_path):
            os.mkdir(self.static_path)

        if self.cmdline_options.io >= 0:
            if not os.path.exists(self.cyclone_io_path):
                os.mkdir(self.cyclone_io_path)

        assert all( os.path.exists(path) for path in
                   (self.root_path, self.install_path, self.glclient_path,
                    self.gldata_path, self.static_path)
                )


# GLSetting is a singleton class exported once
GLSetting = GLSettingsClass()

class transact(object):
    """
    Class decorator for managing transactions.
    Because storm sucks.
    """
    tp = ThreadPool(0, GLSetting.db_thread_pool_size)
    _debug = False

    def __init__(self, method):
        self.method = method
        self.instance = None

    def __get__(self, instance, owner):
        self.instance = instance
        return self

    def __call__(self,  *args, **kwargs):
        return self.run(self._wrap, self.method, *args, **kwargs)

    @property
    def debug(self):
        """
        Whenever you need to trace the database operation on a specific
        function decorated with @transact, just do:
           function.debug = True
           or either
           self.function.debug = True
           or even
           Class.function.debug = True
        """
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = value
        tracer.debug(self._debug, sys.stdout)

    @debug.deleter
    def debug(self):
        self.debug = False

    @staticmethod
    def run(function, *args, **kwargs):
        return deferToThreadPool(reactor, transact.tp, function, *args, **kwargs)

    @staticmethod
    def get_store():
        zstorm = ZStorm()
        zstorm.set_default_uri(GLSetting.store_name, GLSetting.db_file)
        return zstorm.get(GLSetting.store_name)

    def _wrap(self, function, *args, **kwargs):
        self.store = self.get_store()
        try:
            if self.instance:
                result = function(self.instance, self.store, *args, **kwargs)
            else:
                result = function(self.store, *args, **kwargs)
        except (exceptions.IntegrityError, exceptions.DisconnectionError) as e:
            log.msg(e)
            transaction.abort()
            result = None
        except HTTPError as e:
            transaction.abort()
            raise e
        except Exception:
            transaction.abort()
            type, value, tb = sys.exc_info()
            traceback.print_tb(tb, 10)
            self.store.close()
            # propagate the exception
            raise value
        else:
            self.store.commit()
        finally:
            self.store.close()

        return result


transact.tp.start()
reactor.addSystemEventTrigger('after', 'shutdown', transact.tp.stop)

