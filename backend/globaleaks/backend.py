# -*- coding: UTF-8
#   backend
#   *******
# Here is the logic for creating a twisted service. In this part of the code we
# do all the necessary high level wiring to make everything work together.
# Specifically we create the cyclone web.Application from the API specification,
# we create a TCPServer for it and setup logging.
# We also set to kill the threadpool (the one used by Storm) when the
# application shuts down.

import os
import sys

from twisted.application import internet, service
from twisted.internet import reactor, protocol

from twisted.python import log, logfile

from globaleaks.utils.utility import GLLogObserver
from globaleaks.rest import api
from globaleaks.settings import GLSettings


class GLPP(protocol.ProcessProtocol):
    def processExited(self, reason):
        reactor.stop()


application = service.Application('GLBackend')

if not GLSettings.nodaemon and GLSettings.logfile:
    name = os.path.basename(GLSettings.logfile)
    directory = os.path.dirname(GLSettings.logfile)

    gl_logfile = logfile.LogFile(name, directory,
                              rotateLength=GLSettings.log_file_size,
                              maxRotatedFiles=GLSettings.num_log_files)

    application.setComponent(log.ILogObserver, GLLogObserver(gl_logfile).emit)

api_factory = api.get_api_factory()

GLBackendAPI = internet.TCPServer(8083, api_factory)
GLBackendAPI.setServiceParent(application)

battery = os.path.join(os.path.dirname(__file__), 'battery.py')

env = {
  'listening_ips': str(GLSettings.bind_addresses),
  'listening_port': str(GLSettings.bind_port)
}

reactor.spawnProcess(GLPP(),
                     sys.executable,
                     [sys.executable, battery],
                     childFDs={},
                     env=env)
