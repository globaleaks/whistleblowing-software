# -*- coding: UTF-8
#   backend
#   *******
# Here is the logic for creating a twisted service. In this part of the code we
# do all the necessary high level wiring to make everything work together.
# Specifically we create the cyclone web.Application from the API specification,
# we create a TCPServer for it and setup logging.
# We also set to kill the threadpool (the one used by Storm) when the application
# shuts down.

from twisted.internet import reactor

from twisted.application.service import Application
from twisted.application import internet
from cyclone import web
from globaleaks.settings import main
from globaleaks.rest import api

application = Application('GLBackend')

# Initialize the web API event listener, handling all the synchronous operations
GLBackendAPIFactory = web.Application(api.spec, debug=True)
GLBackendAPI = internet.TCPServer(8082, GLBackendAPIFactory)
GLBackendAPI.setServiceParent(application)

# define exit behaviour
reactor.addSystemEventTrigger('after', 'shutdown', main.db_threadpool.stop)
reactor.addSystemEventTrigger('after', 'shutdown', main.scheduler_threadpool.stop)

