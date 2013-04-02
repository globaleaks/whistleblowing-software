# -*- coding: UTF-8
#   config
#   ******
#
# Configuration file do not contain GlobaLeaks Node information, like in the 0.1
# because all those infos are stored in the databased.
# Config contains some system variables usable for debug,

import os
import sys
import shutil
import traceback
import logging
import transaction

import pwd
import grp
import getpass

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

        # daemon
        self.nodaemon = False

        # threads sizes
        self.db_thread_pool_size = 1

        # bind port
        self.bind_port = 8082

        # store name
        self.store_name = 'main_store'

        # files and paths
        self.root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.working_path = os.path.abspath(os.path.join(self.root_path, 'working_dir'))
        self.eval_paths()

        self.receipt_regexp = r'[A-Z]{4}\+[0-9]{5}'

        # list of plugins available in the software
        self.notification_plugins = [
            'MailNotification',
            ]

        # debug defaults
        self.db_debug = True
        self.cyclone_debug = -1
        self.cyclone_debug_counter = 0
        self.loglevel = logging.DEBUG

        # session tracking, in the singleton classes
        self.sessions = dict()

        # value limits in the database
        self.name_limit = 128
        self.description_limit = 1024
        self.generic_limit = 2048

        # static file rules
        self.staticfile_regexp = r'(\w+)\.(\w+)'
        self.staticfile_overwrite = False
        self.reserved_nodelogo_name = "globaleaks_logo" # .png

        # acceptable 'Host:' header in HTTP request
        self.accepted_hosts = "127.0.0.1,localhost"

        # transport security defaults
        self.tor2web_permitted_ops = {
            'admin': False,
            'submission': False,
            'tip': False,
            'receiver': False,
            'unauth': True
        }

        # SOCKS default
        self.socks_host = "127.0.0.1"
        self.socks_port = 9050
        self.tor_socks_enable = True

        self.user = getpass.getuser()
        self.group = getpass.getuser()
        self.uid = os.getuid()
        self.gid = os.getgid()
        self.start_clean = False

        # Expiry time of finalized and not finalized submission,
        # They are copied in a context *when is created*, then
        # changing this variable do not modify the cleaning
        # timings of the existing contexts
        self.tip_seconds_of_life = (3600 * 24) * 15
        self.submission_seconds_of_life = (3600 * 24) * 1
        # enhancement: supports "extended settings in GLCLient"

    def eval_paths(self):
        self.pidfile_path = os.path.join(self.working_path, 'twistd.pid')
        self.glclient_path = os.path.abspath(os.path.join(self.root_path, '..', 'GLClient', 'app'))
        self.gldata_path = os.path.abspath(os.path.join(self.working_path, '_gldata'))
        self.cyclone_io_path = os.path.abspath(os.path.join(self.gldata_path, "cyclone_debug"))
        self.submission_path = os.path.abspath(os.path.join(self.gldata_path, 'submission'))
        self.db_file = 'sqlite:' + os.path.abspath(os.path.join(self.gldata_path,
                                                'glbackend.db'))
        self.db_schema_file = os.path.abspath(os.path.join(self.root_path, 'globaleaks', 'db',
                                           'sqlite.sql'))
        self.static_source = os.path.abspath(os.path.join(self.root_path, 'static'))
        self.static_path = os.path.abspath(os.path.join(self.working_path, '_static'))
        self.logfile = os.path.abspath(os.path.join(self.gldata_path, 'glbackend.log'))

    def load_cmdline_options(self):
        """
        This function is called by runner.py and operate in cmdline_options,
        interpreted and filled in bin/startglobaleaks script.

        happen in startglobaleaks before the sys.argv is modified
        """
        assert self.cmdline_options is not None

        self.nodaemon = self.cmdline_options.nodaemon

        self.db_debug = self.cmdline_options.storm

        self.loglevel = verbosity_dict[self.cmdline_options.loglevel]

        if not self.validate_port(self.cmdline_options.port):
            quit(-1)
        self.bind_port = self.cmdline_options.port

        # If user has requested this option, initialize a counter to
        # record the requests sequence, and setup the logs path
        if self.cmdline_options.io >= 0:
            self.cyclone_debug = self.cmdline_options.io

        if self.cmdline_options.host_list:
            tmp = str(self.cmdline_options.host_list)
            self.accepted_hosts += tmp.replace(" ", "").split(",")

        self.tor_socks_enable = not self.cmdline_options.disable_tor_socks

        if self.cmdline_options.socks_host:
            self.socks_host = self.cmdline_options.socks_host

        if self.cmdline_options.socks_port:
            if not self.validate_port(self.cmdline_options.socks_port):
                quit(-1)
            self.socks_port = self.cmdline_options.socks_port

        if self.cmdline_options.user:
            self.user = self.cmdline_options.user
            self.uid = pwd.getpwnam(self.cmdline_options.user).pw_uid
        else:
            self.uid = os.getuid()

        if self.cmdline_options.group:
            self.group = self.cmdline_options.group
            self.gid = grp.getgrnam(self.cmdline_options.group).gr_gid
        else:
            self.gid = os.getgid()

        if self.uid == 0 or self.gid == 0:
            print "Invalid user: cannot run as root"
            quit(-1)

        self.start_clean = self.cmdline_options.start_clean

        if self.cmdline_options.working_path:
            self.working_path = self.cmdline_options.working_path
            self.eval_paths()

    def validate_port(self, inquiry_port):
        if inquiry_port <= 1024 or inquiry_port >= 65535:
            print "Invalid port number. < of 1024 is not permitted (require"\
                  "root) and > than 65535 can't work"
            return False
        return True


    def create_directories(self):
        """
        Execute some consistency checks on command provided Globaleaks paths

        if one of working_path or static path is created we copy
        here the static files (default logs, and in the future pot files for localization)
        because here stay all the files needed by the application except the python scripts
        """
        new_environment = False

        def create_directory(path):
            # returns false if the directory is already present
            if not os.path.exists(path):
                os.mkdir(path)
                return True
            assert(os.path.isdir(path))
            return False

        if create_directory(self.working_path):
            new_environment = True

        if create_directory(self.static_path):
            new_environment = True

        create_directory(self.gldata_path)
        create_directory(self.submission_path)
        create_directory(self.cyclone_io_path)

        if new_environment:
            for path, subpath, files in os.walk(self.static_source):
                # REMIND: at the moment are not supported subpaths
                for single_file in files:
                    shutil.copyfile(
                        os.path.join(self.static_source, single_file),
                        os.path.join(self.static_path, single_file)
                    )

    def check_directories(self):
        assert all( os.path.exists(path) for path in
                   (self.working_path, self.root_path, self.glclient_path,
                    self.gldata_path, self.static_path, self.submission_path)
                  )

    def remove_directories(self):
        for root, dirs, files in os.walk(self.working_path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

    def drop_privileges(self):
        if os.getgid() == 0 or self.cmdline_options.group:
            print "switching group privileges to %d" % self.gid
            os.setgid(GLSetting.gid)
        if os.getuid() == 0 or self.cmdline_options.user:
            print "switching user privileges to %d" % self.uid
            os.setuid(GLSetting.uid)



# GLSetting is a singleton class exported once
GLSetting = GLSettingsClass()

class transact(object):
    """
    Class decorator for managing transactions.
    Because Storm sucks.
    """
    tp = ThreadPool(0, GLSetting.db_thread_pool_size)
    _debug = False

    def __init__(self, method):
        self.store = None
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
        """
        Setter method for debug property.
        """
        self._debug = value
        tracer.debug(self._debug, sys.stdout)

    @debug.deleter
    def debug(self):
        """
        Deleter method for debug property.
        """
        self.debug = False

    @staticmethod
    def run(function, *args, **kwargs):
        """
        Defer provided function to thread
        """
        return deferToThreadPool(reactor, transact.tp,
                                 function, *args, **kwargs)

    @staticmethod
    def get_store():
        """
        Returns a reference to Storm Store
        """
        zstorm = ZStorm()
        zstorm.set_default_uri(GLSetting.store_name, GLSetting.db_file)
        return zstorm.get(GLSetting.store_name)

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
        except (exceptions.IntegrityError, exceptions.DisconnectionError) as ex:
            log.msg(ex)
            transaction.abort()
            result = None
        except HTTPError as ex:
            transaction.abort()
            raise ex
        except Exception:
            transaction.abort()
            _, exception_value, exception_tb = sys.exc_info()
            traceback.print_tb(exception_tb, 10)
            self.store.close()
            # propagate the exception
            raise exception_value
        else:
            self.store.commit()
        finally:
            self.store.close()

        return result


transact.tp.start()
reactor.addSystemEventTrigger('after', 'shutdown', transact.tp.stop)

