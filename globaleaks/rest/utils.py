from twisted.web import resource
from twisted.python.reflect import prefixedMethodNames

"""
This file contains:

    processChildren
    class parameterHandler(resource.Resource)
        render
"""

__all__ = [ 'processChildren', 'parameterHandler' ]

def processChildren(res, api):
    """
    Used to create the REST handler tree. Goes through the API dictionary and
    finds all the children and binds thier handlers.

    Recursion is beauty.
    """
    for i, a in enumerate(api.items()):
        path, handler = a

        if isinstance(handler, dict):
            # If I am dealing with a dict then I need to pass it through
            # processChildren again (it has children).

            new_res = resource.Resource()
            if hasattr(res, 'path'):
                new_res.path = res.path
            res.putChild(path, processChildren(new_res, handler))

        else:
            # If I am not dealing with a dict then I just need to add the child
            # handler to this particular path.

            # here is instanced the handler object, and then
            # a recurson with processChildern would be started
            res.putChild(path, handler())

            if (len(api) - 1) == i:
                # If I am inside of the leaf of the tree then I need to return
                # (this is needed to make recursion work)
                return res


class parameterHandler(resource.Resource):
    regexp = ''
    isLeaf = True

    def render(self, request):

        m = getattr(self, 'render_' + request.method, None)

        if not m:
            # This needs to be here until the deprecated subclasses of the
            # below three error resources in twisted.web.error are removed.
            from twisted.web.error import UnsupportedMethod
            allowedMethods = (getattr(self, 'allowedMethods', 0) or _computeAllowedMethods(self))
            raise UnsupportedMethod(allowedMethods)

        print request.path.split('/')
        parameter = request.path.split('/')[2]

        print "render: method right:", request, parameter

        return m(request, parameter)

def _computeAllowedMethods(resource):
    """
    Compute the allowed methods on a C{Resource} based on defined render_FOO
    methods. Used when raising C{UnsupportedMethod} but C{Resource} does
    not define C{allowedMethods} attribute.
    """
    allowedMethods = []
    for name in prefixedMethodNames(resource.__class__, "render_"):
        allowedMethods.append(name)
    return allowedMethods


class ErrorPage(resource.Resource):
    """
    L{ErrorPage} is a resource which responds with a particular
    (parameterized) status and a body consisting of HTML containing some
    descriptive text.  This is useful for rendering simple error pages.

    @ivar template: A C{str} which will have a dictionary interpolated into
        it to generate the response body.  The dictionary has the following
        keys:

          - C{"code"}: The status code passed to L{ErrorPage.__init__}.
          - C{"brief"}: The brief description passed to L{ErrorPage.__init__}.
          - C{"detail"}: The detailed description passed to
            L{ErrorPage.__init__}.

    @ivar code: An integer status code which will be used for the response.
    @ivar brief: A short string which will be included in the response body.
    @ivar detail: A longer string which will be included in the response body.
    """

    template = """
<html>
  <head><title>GlobaLeaks backend debug %(code)s - %(brief)s</title></head>
  <body>
    <h1>%(brief)s</h1>
    <p>%(detail)s</p>
  </body>
</html>
"""

    def __init__(self, status, brief, detail):
        Resource.__init__(self)
        self.code = status
        self.brief = brief
        self.detail = detail


    def render(self, request):
        request.setResponseCode(self.code)
        request.setHeader("content-type", "text/html; charset=utf-8")
        return self.template % dict(
            code=self.code,
            brief=self.brief,
            detail=self.detail)


    def getChild(self, chnam, request):
        return self



class NoResource(ErrorPage):
    """
    L{NoResource} is a specialization of L{ErrorPage} which returns the HTTP
    response code I{NOT FOUND}.
    """
    def __init__(self, message="Sorry. No luck finding that resource."):
        ErrorPage.__init__(self, http.NOT_FOUND,
                           "No Such Resource",
                           message)


class ForbiddenResource(ErrorPage):
    """
    L{ForbiddenResource} is a specialization of L{ErrorPage} which returns the
    I{FORBIDDEN} HTTP response code.
    """
    def __init__(self, message="Sorry, resource is forbidden."):
        ErrorPage.__init__(self, http.FORBIDDEN,
                           "Forbidden Resource",
                           message)

