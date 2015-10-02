# -*- coding: UTF-8
#   backend
#   *******
# Here is the logic for creating a twisted service. In this part of the code we
# do all the necessary high level wiring to make everything work together.
# Specifically we create the cyclone web.Application from the API specification,
# we create a TCPServer for it and setup logging.
# We also set to kill the threadpool (the one used by Storm) when the
# application shuts down.

from twisted.application import internet, service

from globaleaks.rest import api
from globaleaks.settings import GLSettings

application = service.Application('GLBackend')
api_factory = api.get_api_factory()

for ip in GLSettings.bind_addresses:
    GLBackendAPI = internet.TCPServer(GLSettings.bind_port, api_factory, interface=ip)
    GLBackendAPI.setServiceParent(application)

# define exit behaviour
