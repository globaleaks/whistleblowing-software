import json
from twisted.web import resource
from globaleaks.rest.handlers import *
from globaleaks.rest.utils import processChildren

__all__ = ['RESTful', 'attach_rest' ]

"""
This file contains:

    class RESTful(resource.Resource)
        getChild
"""

"""
http://twistedmatrix.com/documents/12.1.0/api/twisted.web.resource.IResource.html
"""
class RESTful(resource.Resource):


    def __init__(self, APImap):
        """
        Create the root of the restful interface and create the children
        handlers for handlers that don't take a parameter.

        APImap is a dict collected by all the modules that want
        expose a REST interface
        """
        resource.Resource.__init__(self)

        # this function is in utils.py, and is a recursive function
        processChildren(self, APImap)

        # call the module(s) that load REST interface
        from globaleaks.rest.external_loader import simulation_of_module_loading_rest
        simulation_of_module_loading_rest()

    def getChild(self, path, request):
        """
        When trying to access a child that does not exist return an empty
        resource.
        This method is overriden when you need to handle 'stuff/$random/child'
        """
        print "(default error ?) getChild ", path, request
        return resource.Resource()


"""
The follwing part of code is intended to be moved in the
backend/core logic, and implemented here just for 
"""

if __name__ == "__main__":

    from twisted.internet import reactor
    from twisted.web import server


    # not all APIs are know at the start of the software,
    # modules can implement their own REST
    
    tipAPImap = { 
            'download_material': downloadMaterialHandler,
            'add_comment': addCommentHandler,
            'pertinence': pertinenceHandler,
            'add_description': addDescriptionHandler
                }

    adminAPImap = { 
           'contexts': ContextHandler,
           'node': NodeHandler,
           'group' : GroupHandlers,        # WC
           'receivers': ReceiversHandlers, # WC
           'modules': ModulesHandlers      # WC 
        }

    APImap = {
       'node': nodeHandler,
       'submission': submissionHandlers, # wildcard handling 
       'tip': tipAPImap, # tipHandlers,   # handle the default path
       'admin': adminAPImap, #  adminHandlers, # too
       'receiver' : receiverHandlers # too!
    }

    print "\n"
    print "adminAPImap", len(adminAPImap)
    print "APImap", len(APImap)
    print "tipAPImap", len(tipAPImap)
    #APImap.update(tipAPImap)
    #APImap.update(adminAPImap)
    print "sum:", len(APImap)

    for k, v in APImap.items():
        if isinstance(v, dict):
            print k
            for sk, sv in v.items():
                print "\t",sk," => ", str(sv)
        else:
            print k," => ", str(v)

    reactor.listenTCP(8082, server.Site(RESTful(APImap)))
    reactor.run()


# ORIGINAL API MAP
#    APImap = {
#       'node': nodeHandler,
#       'submission': submissionHandlers,        # wildcard handling (WC)
#       'tip': tipHandlers,                      # WC
#       'admin': { 
#           'contexts': adminContextHandler,
#           'node': adminNodeHandler,
#           'group' : adminGroupHandlers,        # WC
#           'receivers': adminReceiversHandlers, # WC
#           'modules': adminModulesHandlers      # WC 
#                }
#    }

