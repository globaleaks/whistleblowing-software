from twisted.web import resource

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

        print "X: called render in", self.__class__.__name__, request.method, request

        m = getattr(self, 'render_' + request.method, None)

        print self.__class__.__name__ + str(m)

        if not m:
            # This needs to be here until the deprecated subclasses of the
            # below three error resources in twisted.web.error are removed.
            from twisted.web.error import UnsupportedMethod
            allowedMethods = (getattr(self, 'allowedMethods', 0) or _computeAllowedMethods(self))
            raise UnsupportedMethod(allowedMethods)

        parameter = request.path.split('/')[2]

        print "render: method right:", str(m), request, parameter

        return m(request, parameter)


