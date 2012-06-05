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

__all__ = ['infoHandler','nodeHandler','submissionHandler',
           'adminReceiversHandler', 'nodeConfigHandler',
           'deliveryConfigHandler', 'storageConfigHandler',
           'parameterHandler', 'addCommentHandler', 'pertinenceHandler',
           'downloadMaterialHandler', 'addDescriptionHandler', 'tipHandler']

class infoHandler(resource.Resource):
    def __init__(self, name="default"):
        self.name = name
        resource.Resource.__init__(self)

    def render_GET(self, request):
        return json.dumps(API.keys())

    def render_POST(self, request):
        pass

class nodeHandler(resource.Resource):
    def render_GET(self, request):
        return str(self.__class__)

class submissionHandler(resource.Resource):
    def render_GET(self, request):
        return str(self.__class__)

class adminReceiversHandler(resource.Resource):
    def render_GET(self, request):
        return str(self.__class__)

class nodeConfigHandler(resource.Resource):
    def render_GET(self, request):
        return str(self.__class__)

class deliveryConfigHandler(resource.Resource):
    def render_GET(self, request):
        return str(self.__class__)

class storageConfigHandler(resource.Resource):
    def render_GET(self, request):
        return str(self.__class__)

# Tip Handlers

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

tipAPI = {'download_material': downloadMaterialHandler,
          'add_comment': addCommentHandler,
          'pertinence': pertinenceHandler,
          'add_description': addDescriptionHandler}


class tipHandler(resource.Resource):
    path = 'default'

    def __init__(self):
        resource.Resource.__init__(self)
        processChildren(self, tipAPI)

    def getChild(self, path, request):
        print "Got child request!"
        return tipHandler()

