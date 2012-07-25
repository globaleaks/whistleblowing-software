import json
from twisted.web import resource

from globaleaks.rest.handlers import *
from globaleaks.rest.utils import processChildren
import pdb

class RESTful(resource.Resource):

    APImap = {
       'node': nodeHandler,
       'submission': submissionHandlers,        # wildcard handling (WC)
       'tip': tipHandlers,                      # WC
       'admin': { 
           'contexts': adminContextHandler,
           'node': adminNodeHandler,
           'group' : adminGroupHandlers,        # WC
           'receivers': adminReceiversHandlers, # WC
           'modules': adminModulesHandlers      # WC 
                }
    }

    def __init__(self):
        """
        Create the root of the restful interface and create the children
        handlers for handlers that don't take a parameter.
        """
        resource.Resource.__init__(self)
        processChildren(self, self.APImap)

    def getChild(self, path, request):
        """
        When trying to access a child that does not exist return an empty
        resource.
        """
        print "getChild ", path, request
        return resource.Resource()

if __name__ == "__main__":

    from twisted.internet import reactor
    from twisted.web import server

    reactor.listenTCP(8082, server.Site(RESTful()))
    reactor.run()
