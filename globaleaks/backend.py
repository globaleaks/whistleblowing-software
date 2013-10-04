# -*- coding: UTF-8
#   backend
#   *******
# Here is the logic for creating a twisted service. In this part of the code we
# do all the necessary high level wiring to make everything work together.
# Specifically we create the cyclone web.Application from the API specification,
# we create a TCPServer for it and setup logging.
# We also set to kill the threadpool (the one used by Storm) when the
# application shuts down.

from twisted.application.service import Application
from twisted.application import internet
from cyclone import web
from globaleaks.settings import GLSetting
from globaleaks.rest import api
from globaleaks.handlers.base import GLHTTPServer

from Crypto.Random import random

application = Application('GLBackend')

settings = dict(cookie_secret=random.getrandbits(128),
                xsrf_cookies=True,
                debug=GLSetting.http_log)

# Initialize the web API event listener, handling all the synchronous operations
GLBackendAPIFactory = web.Application(api.spec, **settings)
GLBackendAPIFactory.protocol = GLHTTPServer

for ip in GLSetting.bind_addresses:
    GLBackendAPI = internet.TCPServer(GLSetting.bind_port, GLBackendAPIFactory, interface=ip)
    GLBackendAPI.setServiceParent(application)

# define exit behaviour

