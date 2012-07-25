"""
    Handler
    *******

    This contains all of the handlers for the REST interface.
    Should not contain any logic that is specific to the operations to be done
    by the particular REST interface.
"""
import json
from twisted.web import resource
from globaleaks.rest.utils import processChildren

__all__ = [ 'nodeHandler', 'submissionHandlers', 'tipHandlers',
            'adminContextHandler', 'adminNodeHandler', 'adminGroupHandlers', 
            'adminReceiversHandlers', 'adminModulesHandlers' ]

class nodeHandler(resource.Resource):
    def __init__(self, name="default"):
        self.name = name
        resource.Resource.__init__(self)

    def render_GET(self, request):
        print "infoHandler " + "GET"
        return json.dumps(API.keys())

    def render_POST(self, request):
        print "infoHandler " + "POST"
        pass

class nodeHandler(resource.Resource):
    def render_GET(self, request):
        return str(self.__class__)

class submissionHandlers(resource.Resource):
    def render_GET(self, request):
        return str(self.__class__)

class adminContextHandler(resource.Resource):
    def render_GET(self, request):
        return str(self.__class__)

class adminNodeHandler(resource.Resource):
    def render_GET(self, request):
        return str(self.__class__)

class adminGroupHandlers(resource.Resource):
    def render_GET(self, request):
        print "admin group hahaha"
        import pdb
        #pdb.set_trace()
        return str(self.__class__)

class adminReceiversHandlers(resource.Resource):
    def render_GET(self, request):
        return str(self.__class__)

class adminModulesHandlers(resource.Resource):
    def render_GET(self, request):
        return str(self.__class__)

# Follow the Tip Handlers, 

class parameterHandler(resource.Resource):
    regexp = ''
    isLeaf = True
    def render(self, request):
        m = getattr(self, 'render_' + request.method, None)
        if not m:
            # This needs to be here until the deprecated subclasses of the
            # below three error resources in twisted.web.error are removed.
            from twisted.web.error import UnsupportedMethod
            allowedMethods = (getattr(self, 'allowedMethods', 0) or
                              _computeAllowedMethods(self))
            raise UnsupportedMethod(allowedMethods)
        parameter = request.path.split('/')[2]
        return m(request, parameter)

class addCommentHandler(parameterHandler):
    def render_GET(self, request, parameter):
        return str(self.__class__) + "<br>" + parameter

class pertinenceHandler(parameterHandler):
    def render_GET(self, request, parameter):
        return str(self.__class__) + "<br>" + parameter

class downloadMaterialHandler(parameterHandler):
    def render_GET(self, request, parameter):
        return str(self.__class__) + "<br>" + parameter

class addDescriptionHandler(parameterHandler):
    def render_GET(self, request, parameter):
        return str(self.__class__)


class tipHandlers(resource.Resource):
    path = 'default'

    tipAPImap = { 'download_material': downloadMaterialHandler,
              'add_comment': addCommentHandler,
              'pertinence': pertinenceHandler,
              'add_description': addDescriptionHandler}

    def __init__(self):
        resource.Resource.__init__(self)
        processChildren(self, self.tipAPI)

    def getChild(self, path, request):
        print "Got child request!"
        return tipHandlers()
