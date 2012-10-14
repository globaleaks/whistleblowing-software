# -*- coding: UTF-8
#   backend
#   *******
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
import sys
import os

# hack to add globaleaks to the sys path
# this would avoid export PYTHONPATH=`pwd`
#cwd = '/'.join(__file__.split('/')[:-1])
#sys.path.insert(0, os.path.join(cwd, '../'))

from twisted.internet.defer import inlineCallbacks

from globaleaks.utils import logging
from globaleaks.utils.logging import log

from globaleaks.db import createTables, threadpool
from globaleaks.rest import api

from twisted.application import service, internet, app

from twisted.internet import reactor
from twisted.python import log, util
from cyclone.web import Application

from twisted.python.log import ILogObserver, FileLogObserver, _safeFormat
from twisted.python.logfile import DailyLogFile

application = service.Application('GLBackend')
GLBackendAPIFactory = Application(api.spec, debug=True)
GLBackendAPI = internet.TCPServer(8082, GLBackendAPIFactory)
GLBackendAPI.setServiceParent(application)

# XXX make this a config option
log_file = "/tmp/glbackend.log"

log_folder = os.path.join('/', *log_file.split('/')[:-1])
log_filename = log_file.split('/')[-1]
daily_logfile = DailyLogFile(log_filename, log_folder)
log.addObserver(FileLogObserver(daily_logfile).emit)

reactor.addSystemEventTrigger('after', 'shutdown', threadpool.stop)
