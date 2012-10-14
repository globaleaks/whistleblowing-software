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
from twisted.python import log
from cyclone.web import Application

from twisted.python.log import ILogObserver, FileLogObserver
from twisted.python.logfile import DailyLogFile

application = service.Application('GLBackend')
GLBackendAPIFactory = Application(api.spec, debug=True)
GLBackendAPI = internet.TCPServer(8082, GLBackendAPIFactory)
GLBackendAPI.setServiceParent(application)

logfile = DailyLogFile("glbackend.log", "/tmp")
application.setComponent(ILogObserver, FileLogObserver(logfile).emit)

reactor.addSystemEventTrigger('after', 'shutdown', threadpool.stop)
