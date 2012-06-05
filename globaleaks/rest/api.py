import json
from twisted.web import resource

#from globaleaks.tip import tipHandler
#from globaleaks.receivers import groupsHandler, receiversHandler
#from globaleaks.stats import statsHandler
#from globaleaks.admin import adminHandler
from globaleaks.rest.handlers import *
from globaleaks.rest.utils import processChildren

class RESTful(resource.Resource):
    API = {
       'node': nodeHandler,
       'submission': submissionHandler, # wildcard handling
       'tip': tipHandler,               # wildcard handling
       'admin': {'receivers': adminReceiversHandler,
                 'config':  {'node': nodeConfigHandler,
                             'delivery': deliveryConfigHandler,
                             'storage': storageConfigHandler
                            }
                }
    }

    def __init__(self):
        """
        Create the root of the restful interface and create the children
        handlers for handlers that don't take a parameter.
        """
        resource.Resource.__init__(self)
        processChildren(self, self.API)

    def getChild(self, path, request):
        """
        When trying to access a child that does not exist return an empty
        resource.
        """
        print path, request
        return resource.Resource()

if __name__ == "__main__":
    from twisted.internet import reactor
    from twisted.web import server
    reactor.listenTCP(8082, server.Site(RESTful()))
    reactor.run()


def processChildren(res, api):
    """
    Recursion is beauty.
    """
    for i, a in enumerate(api.items()):
        path, handler = a
        #print i
        if isinstance(handler, dict):
            #print "Got the dict :("
            #print "Res: %s" % res
            #print "Path: %s" % path
            #print "Handler: %s" % handler
            new_res = resource.Resource()
            if hasattr(res, 'path'):
                new_res.path = res.path
            res.putChild(path, processChildren(new_res, handler))

        else:
            #print "Got the handler ;)"
            #print "Res: %s" % res
            #print "Path: %s" % path
            #print "Handler: %s" % handler
            res.putChild(path, handler())
            if (len(api) - 1) == i:
                return res

