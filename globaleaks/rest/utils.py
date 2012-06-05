from twisted.web import resource

def processChildren(res, api):
    """
    Used to create the REST handler tree. Goes through the API dictionary and
    finds all the children and binds thier handlers.

    Recursion is beauty.
    """
    for i, a in enumerate(api.items()):
        path, handler = a
        #print i
        if isinstance(handler, dict):
            # If I am dealing with a dict then I need to pass it through
            # processChildren again (it has children).
            #
            #print "Got the dict :("
            #print "Res: %s" % res
            #print "Path: %s" % path
            #print "Handler: %s" % handler
            new_res = resource.Resource()
            if hasattr(res, 'path'):
                new_res.path = res.path
            res.putChild(path, processChildren(new_res, handler))

        else:
            # If I am not dealing with a dict then I just need to add the child
            # handler to this particular path.
            #
            #print "Got the handler ;)"
            #print "Res: %s" % res
            #print "Path: %s" % path
            #print "Handler: %s" % handler
            res.putChild(path, handler())
            if (len(api) - 1) == i:
                # If I am inside of the leaf of the tree then I need to return
                # (this is needed to make recursion work)
                return res

