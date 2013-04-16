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
import socket

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
    'DEBUG': logging.DEBUG,
    'INFO' : logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

class GLSettingsClass:

    def __init__(self):
        # command line parsing utils
        self.parser = OptionParser()
        self.cmdline_options = None

        # version
        self.version_string = "0.2.0"

        # daemon
        self.nodaemon = False

        # threads sizes
        self.db_thread_pool_size = 1

        # bind port
        self.bind_port = 8082

        # store name
        self.store_name = 'main_store'

        # unhandled Python Exception are reported via mail
        self.error_reporting_username= "stackexception@globaleaks.org"
        self.error_reporting_password= "stackexception99"
        self.error_reporting_server = "box549.bluehost.com"
        self.error_reporting_port = 25
        self.error_reporting_destmail = "stackexception@lists.globaleaks.org"

        # files and paths
        self.root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.working_path = os.path.abspath(os.path.join(self.root_path, 'nodedata'))
        self.eval_paths()

        self.receipt_regexp = r'[A-Z]{4}\+[0-9]{5}'

        # list of plugins available in the software
        self.notification_plugins = [
            'MailNotification',
            ]

        # debug defaults
        self.db_debug = False
        self.cyclone_debug = -1
        self.cyclone_debug_counter = 0
        self.loglevel = "CRITICAL"

        # session tracking, in the singleton classes
        self.sessions = dict()

        # value limits in the database
        self.name_limit = 128
        self.description_limit = 1024
        self.generic_limit = 2048
        self.max_file_size = (30 * 1024 * 1024) # 30 Mb

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
        self.tip_seconds_of_life = 240 # (3600 * 24) * 15
        self.submission_seconds_of_life = 120 # (3600 * 24) * 1
        # enhancement: supports "extended settings in GLCLient"

        # Number of failed login enough to generate an alarm
        self.failed_login_alarm = 5

        # Size in bytes of every log file. Once this size is reached the
        # logfile is rotated.
        # Default: 1M
        self.log_file_size = 1000000
        # Number of log files to conserve.
        self.maximum_rotated_log_files = 100


    def eval_paths(self):
        self.pidfile_path = os.path.join(self.working_path, 'twistd.pid')
        self.glclient_path = os.path.abspath(os.path.join('/usr/share/globaleaks', 'glclient'))
        self.glfiles_path = os.path.abspath(os.path.join(self.working_path, 'files'))
        self.gldb_path = os.path.abspath(os.path.join(self.working_path, 'db'))
        self.log_path = os.path.abspath(os.path.join(self.working_path, 'log'))
        self.cyclone_io_path = os.path.abspath(os.path.join(self.log_path, "jsondump"))
        self.submission_path = os.path.abspath(os.path.join(self.glfiles_path, 'submission'))
        self.static_source = os.path.abspath(os.path.join(self.root_path, 'staticdata'))
        self.static_path = os.path.abspath(os.path.join(self.glfiles_path, 'static'))
        self.static_db_source = os.path.abspath(os.path.join(self.root_path, 'globaleaks', 'db'))

        self.db_file = 'sqlite:' + os.path.abspath(os.path.join(self.gldb_path, 'glbackend.db'))
        self.db_schema_file = os.path.join(self.static_db_source,'sqlite.sql')
        self.logfile = os.path.abspath(os.path.join(self.log_path, 'globaleaks.log'))

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

        self.cyclone_debug = self.cmdline_options.io

        self.accepted_hosts = self.cmdline_options.host_list.replace(" ", "").split(",")

        self.tor_socks_enable = not self.cmdline_options.disable_tor_socks

        self.socks_host = self.cmdline_options.socks_host

        if not self.validate_port(self.cmdline_options.socks_port):
            quit(-1)
        self.socks_port = self.cmdline_options.socks_port

        if self.tor_socks_enable:
            # convert socks addr in IP and perform a test connection
            self.validate_socks()

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

        self.twistd_log = self.cmdline_options.twistd_log
        self.start_clean = self.cmdline_options.start_clean

        self.working_path = self.cmdline_options.working_path
        self.eval_paths()

    def validate_port(self, inquiry_port):
        if inquiry_port >= 65535 or inquiry_port < 0:
            print "Invalid port number ( > than 65535 can't work! )"
            return False
        return True

    def validate_socks(self):
        """
        Convert eventually hostname to IPv4 address format and then perform
        a test connection at them. Need to simply perform a validation of the
        socks and their reachability
        """
        try:
            ip_safe_socks_host = socket.gethostbyname(self.socks_host)
            self.socks_host = ip_safe_socks_host
        except Exception as excep:
            print "Invalid host %s: %s" % (self.socks_host, excep.strerror)
            quit(-1)

        testconn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        testconn.setblocking(0)
        testconn.settimeout(1.5) # 1.5 seconds to reach your socks
        try:
            testconn.connect((self.socks_host, self.socks_port))
        except Exception as excep:
            if hasattr(excep, 'strerror') and len(excep.strerror) > 1:
                err_info = excep.strerror
            else:
                err_info = excep.message
            print "Unable to connect to Tor socks at %s:%d (%s)" %\
                  (self.socks_host, self.socks_port, err_info)
            quit(-1)


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
                try:
                    os.mkdir(path)
                    self.log_debug("Created directoy %s" % path)
                    return True
                except OSError as excep:
                    self.log_debug("Error in creating directory: %s (%s)" % (path, excep.strerror))
                    raise excep
            else:
                if not os.path.isdir(path):
                    self.log_debug("Error creating directory: %s (path exists and is not a dir)" % path)
                    raise Exception("Error creating directory: %s (path exists and is not a dir)" % path)
                return False

        if create_directory(self.working_path):
            new_environment = True

        if create_directory(self.gldb_path):
            new_environment = True

        create_directory(self.glfiles_path)

        if create_directory(self.static_path):
            new_environment = True

        create_directory(self.submission_path)
        create_directory(self.log_path)

        if self.cyclone_debug >= 0:
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
        for path in (self.working_path, self.root_path, self.glclient_path,
                     self.glfiles_path, self.static_path, self.submission_path, self.log_path):
            if not os.path.exists(path):
                raise Exception("%s does not exists!" % path)

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

    def log_debug(self, message):
        """
        Log to stdout only if debug is set at higher levels
        """
        if self.loglevel == logging.DEBUG:
            print message



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

