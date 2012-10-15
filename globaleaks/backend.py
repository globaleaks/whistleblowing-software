# -*- coding: UTF-8
#   backend
#   *******
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>
#            Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#

"""
Here is the logic for creating a twisted service. In this part of the code we
do all the necessary high level wiring to make everything work together.
Specifically we create the cyclone web.Application from the API specification,
we create a TCPServer for it and setup logging.

We also set to kill the threadpool (the one used by Storm) when the application
shuts down.
"""

import os

# hack to add globaleaks to the sys path
# this would avoid export PYTHONPATH=`pwd`
#cwd = '/'.join(__file__.split('/')[:-1])
#sys.path.insert(0, os.path.join(cwd, '../'))

from twisted.internet import reactor

from twisted.application.service import Application
from twisted.application import internet

from cyclone import web

from globaleaks import db_threadpool, scheduler_threadpool
from globaleaks.rest import api

from globaleaks.utils import log

application = Application('GLBackend')
GLBackendAPIFactory = web.Application(api.spec, debug=True)
GLBackendAPI = internet.TCPServer(8082, GLBackendAPIFactory)
GLBackendAPI.setServiceParent(application)

reactor.addSystemEventTrigger('after', 'shutdown', db_threadpool.stop)
reactor.addSystemEventTrigger('after', 'shutdown', db_threadpool.stop)
