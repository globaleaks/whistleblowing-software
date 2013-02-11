# -*- encoding: utf-8 -*-
#
# Log observer, need to be extended to report
# application error in an appropriate DB table, and
# need to be enable by the config options

import sys
import os
import logging

from twisted.python import log as txlog
from twisted.python.logfile import DailyLogFile

from globaleaks.utils import gltime
from globaleaks import settings

# XXX make this a config option
log_file = "/tmp/glbackend.log"

log_folder = os.path.join('/', *log_file.split('/')[:-1])
log_filename = log_file.split('/')[-1]
daily_logfile = DailyLogFile(log_filename, log_folder)

class LoggerFactory(object):
    def __init__(self, options):
        #print options
        pass

    def start(self, application):
        txlog.msg("Starting GLBackend on %s (%s UTC)" %  (gltime.prettyDateNow(),
                                                        gltime.utcPrettyDateNow()))
        logging.basicConfig()
        python_logging = txlog.PythonLoggingObserver()
        if settings.config.advanced.debug:
            python_logging.logger.setLevel(logging.DEBUG)
        else:
            python_logging.logger.setLevel(logging.INFO)

        txlog.startLoggingWithObserver(python_logging.emit)

        txlog.addObserver(txlog.FileLogObserver(daily_logfile).emit)

    def stop(self):
        txlog.msg("Stopping GLBackend")

def msg(msg, *arg, **kw):
    txlog.msg(msg, logLevel=logging.INFO, *arg, **kw)

def debug(msg, *arg, **kw):
    txlog.msg(msg, logLevel=logging.DEBUG, *arg, **kw)

def err(msg, *arg, **kw):
    txlog.err(msg, logLevel=logging.ERROR, *arg, **kw)

def exception(*msg):
    logging.exception(msg)
