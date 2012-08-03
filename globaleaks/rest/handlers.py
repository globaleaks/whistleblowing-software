"""
    Handler
    *******

    This contains all of the handlers for the REST interface.
    Should not contain any logic that is specific to the operations to be done
    by the particular REST interface.

    It's simply implement the inteface 
"""
import json
from twisted.web import resource
from globaleaks.rest.utils import processChildren, parameterHandler

__all__ = [ 'nodeHandler', 'submissionHandlers', 'receiverHandlers',
            # follow "admin" block of handlers
            'adminHandlers',
            'ContextHandler', 'NodeHandler', 'GroupHandlers', 
            'ReceiversHandlers', 'ModulesHandlers',
            # follow "tip" block of handlers
            'tipHandlers',
            'downloadMaterialHandler', 'addCommentHandler',
            'pertinenceHandler', 'addDescriptionHandler' ]

class nodeHandler(resource.Resource):

#    def __init__(self, name="default"):
#        self.name = name
#        resource.Resource.__init__(self)

    def render_GET(self, request):
        print "infoHandler GET", str(request)
        return "infoHandler GET" + str(request)

    def render_POST(self, request):
        print "infoHandler POST", str(request)
        return "infoHandler POST" + str(request)

class submissionHandlers(resource.Resource):
    def render_GET(self, request):
        return str(self.__class__.__name__ )

class receiverHandlers(resource.Resource):
    def render_GET(self, request):
        return str(self.__class__.__name__ )

# Follow the Admin Handlers
class adminHandlers(resource.Resource):
    path = 'default'

    def __init__(self):
        print "init of adminHandlers"
        resource.Resource.__init__(self)

    def getChild(self, path, request):
        print self.__class__.name, "Got child request!", path, request
        return adminHandlers()

class ContextHandler(parameterHandler):
    def render_GET(self, request, parameter):
        return str(self.__class__.__name__) + request + parameter

class NodeHandler(parameterHandler):
    def render_GET(self, request, parameter):
        return str(self.__class__.__name__) + request + parameter

class GroupHandlers(parameterHandler):
    def render_GET(self, request, parameter):
        print "GET", request.path
        print type(parameter)
        print parameter
        return "test GET & parm" + request.path + ", " + parameter

    def render_POST(self, request, parameter):
        print "POST", request.path
        print type(parameter)
        print parameter
        return "test POST & parm" + request.path + ", " + parameter

class ReceiversHandlers(parameterHandler):
    def render_GET(self, request, parameter):
        return str(self.__class__.__name__) + request + parameter

class ModulesHandlers(parameterHandler):
    def render_GET(self, request, parameter):
        return str(self.__class__.__name__) + request + parameter
#############################################


# Follow the Tip Handlers, 
class tipHandlers(resource.Resource):
    path = 'default'

    def __init__(self):
        resource.Resource.__init__(self)

        # Tip can be expanded by a module, then in this 
        # point, the module list need to be already loaded, 
        # because here is request if other REST would be exposed.

        """
        tipAPImap = { 
            'download_material': downloadMaterialHandler,
            'add_comment': addCommentHandler,
            'pertinence': pertinenceHandler,
            'add_description': addDescriptionHandler
                }

        processChildren(self, self.tipAPImap)
        """

    def getChild(self, path, request):
        print self.__class__.name, "Got child request!", path, request
        return tipHandlers()


class addCommentHandler(parameterHandler):

    def render_GET(self, request, parameter):
        return "GET " + str(self.__class__) + "<br>" + parameter

    def render_POST(self, request, parameter):
        return "POST " + str(self.__class__) + "<br>" + parameter

class pertinenceHandler(parameterHandler):

    def render_GET(self, request, parameter):
        return "GET " + str(self.__class__) + "<br>" + parameter

    def render_POST(self, request, parameter):
        return "POST " + str(self.__class__) + "<br>" + parameter

class downloadMaterialHandler(parameterHandler):

    def render_GET(self, request, parameter):
        return "GET " + str(self.__class__) + "<br>" + parameter

    def render_POST(self, request, parameter):
        return "POST " + str(self.__class__) + "<br>" + parameter

class addDescriptionHandler(parameterHandler):

    def render_GET(self, request, parameter):
        return "GET " + str(self.__class__) + "<br>" + parameter

    def render_POST(self, request, parameter):
        return "POST " + str(self.__class__) + "<br>" + parameter

#############################################
