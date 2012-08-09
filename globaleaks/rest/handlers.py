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
from globaleaks.utils.JSONhelper import genericDict

__all__ = [ 'nodeHandler', 
                # single, P1
            'submissionHandlers', 
                # (parameter  + fixed), P2-P7
            'receiverHandlers',
                # (parameter + parameter) and (parameter + fixed), R1-R2
            'adminHandlers',
                # generic handler of /admin/ resource
            'ContextHandler', 'NodeHandler', 'GroupHandlers', 
            'ReceiversHandlers', 'ModulesHandlers',
                # (parameter + fixed), A1-A5
            'tipHandlers',
            'downloadMaterialHandler', 'addCommentHandler',
            'pertinenceHandler', 'addDescriptionHandler' 
                # Tip handler (implemented as external REST), T1-T6
                # XXX - not yet externalized, the external one is /external_test/
            ]

"""
Public resource (P1) /node/ return a general amount of info
"""
class nodeHandler(parameterHandler):

    def __init__(self, name="default"):
        self.name = name
        print "iniziato ortomio"
        resource.Resource.__init__(self)

    def render_GET(self, request, parameter):
        print type(request)
        print type(parameter)
        print "nodeHandler (public info) GET:" + request.path 

        retjson = genericDict('render_GET_P1')
        retjson.add_string('FunkyNodeName', 'name')
        retjson.add_string('statz', 'statistic')
        retjson.add_string('BOOLofPROPERTIES', 'node_properties')
        retjson.add_string('This is the description', 'description')
        retjson.add_string('http://funkytransparency.pin', 'public_site')
        retjson.add_string('http://nf940289fn24fewifnm.onion', 'hidden_service')
        retjson.add_string('/', 'url_schema')
        return retjson.printJSON()

        """
        retDict = dict({'expected_result' : ({ "name": "string", "statistics": "S_nodeStatisticsDict", 
                        "node_properties": "S_nodePropertiesDict",
                        "contexts": [ "A_contextDescriptionDict" ],
                        "description": "F_localizationDict(nodeDesc)",
                        "public_site": "string", "hidden_service": "string", "url_schema": "string" })
                      })
        print retDict
        """

class submissionHandlers(resource.Resource):
    def render_GET(self, request):
        return str(self.__class__.__name__ )

class receiverHandlers(resource.Resource):
    def render_GET(self, request):
        return str(self.__class__.__name__ )

##############################################################
# Follow the Admin Handlers
class adminHandlers(resource.Resource):
    path = 'default'

    def __init__(self):
        print "init of adminHandlers"
        resource.Resource.__init__(self)

    def getChild(self, path, request):
        print self.__class__.name, "ADMIN Got child request!", path, request
        return adminHandlers()

"""
NodeHandler part of adminHandlers covert, /admin/node
do not expect a parameter. handle READ and SET
A1
"""
class NodeHandler(parameterHandler):
    def render_GET(self, request, parameter):
        """
        return the information of the node, various blob of data
        object contained: nodeStatisticDict, nodePropertiesDict,
        contextDescription (array of), localizationDict
        """
        print "node GET:" + request.path 
        return "node GET:" + request.path 


    def render_POST(self, request, parameter):
        """
        await partially the data returned by GET, and some node 
        specific configuration.
        """
        print "node POST:" + request.path 
        return "node POST:" + request.path


"""
ContextHandler part of adminHandlers covert /admin/contexts CURD
A2
"""
class ContextHandler(parameterHandler):

    def render_GET(self, request, parameter):
        """
        return array of contextDescriptionDict
        """
        print "context GET:" + request.path + ", " + parameter
        return "context GET:" + request.path + ", " + parameter

    def render_POST(self, request, parameter):
        """
        check 'create' or 'delete' and wait a
        contextDescriptionDict to be updated
        return as get or errors
        """
        print "context POST:" + request.path + ", " + parameter
        return "context POST:" + request.path + ", " + parameter

    def render_PUT(self, request, parameter):
        """
        await a context to add, and assign an ID
        return as get or errors
        """
        print "context PUT:" + request.path + ", " + parameter
        return "context PUT:" + request.path + ", " + parameter


    def render_DELETE(self, request, parameter):
        """
        await a context to delete, check if exists
        return as get or errors
        """
        print "context DELETE:" + request.path + ", " + parameter
        return "context DELETE:" + request.path + ", " + parameter

    def getChild(self, path, request):
        print self.__class__.name, "GroupH child request!", path, request


"""
GroupHandler part of adminHandlers covert 
/admin/groups/<context_$ID> CURD
A3
"""
class GroupHandlers(parameterHandler):
    def render_GET(self, request, parameter):
        """
        return two Arrays, groupDescriptionDict
        and modules_available (moduleDataDict)
        """
        print "GroupH GET:" + request.path + ", " + parameter
        return "GroupH GET:" + request.path + ", " + parameter

    def render_POST(self, request, parameter):
        """
        check 'create' or 'delete' and wait a
        groupDescriptionDict to be updated
        return as get
        """
        print "GroupH POST:" + request.path + ", " + parameter
        return "GroupH POST:" + request.path + ", " + parameter

    def render_PUT(self, request, parameter):
        """
        await a groupDescriptionDict, verify, create ID
        return as get
        """
        print "GroupH PUT:" + request.path + ", " + parameter
        return "GroupH PUT:" + request.path + ", " + parameter


    def render_DELETE(self, request, parameter):
        """
        await a valid groupDescriptionDict,
        return as get or error if ID is missing
        """
        print "GroupH DELETE:" + request.path + ", " + parameter
        return "GroupH DELETE:" + request.path + ", " + parameter

    def getChild(self, path, request):
        print self.__class__.name, "GroupH child request!", path, request
        return GroupHandlers()


"""
ReceiverHandlers part of adminHandlers covers
/admin/receivers/<group_$ID> A4
"""
class ReceiversHandlers(parameterHandler):
    def render_GET(self, request, parameter):
        """
        return Array of receiverDescriptionDict,
        """
        print "RecvH GET:" + request.path + ", " + parameter
        return "RecvH GET:" + request.path + ", " + parameter

    def render_POST(self, request, parameter):
        """
        check 'create' or 'delete' and wait a
        receiverDescriptionDict to be updated
        return as get
        """
        print "RecvH POST:" + request.path + ", " + parameter
        return "RecvH POST:" + request.path + ", " + parameter

    def render_PUT(self, request, parameter):
        """
        await a receiverDescriptionDict, verify, create
        return as get
        """
        print "RecvH PUT:" + request.path + ", " + parameter
        return "RecvH PUT:" + request.path + ", " + parameter


    def render_DELETE(self, request, parameter):
        """
        await a valid groupDescriptionDict,
        return as get or error if ID is missing
        """
        print "RecvH DELETE:" + request.path + ", " + parameter

    def getChild(self, path, request):
        print self.__class__.name, "RECEIVER child request!", path, request
        return ReceiversHandlers()

"""
ModulesHandlers handle /admin/modules/<string module_type> A5
"""
class ModulesHandlers(parameterHandler):
    def render_GET(self, request, parameter):
        """
        return the list of module present in a node,
        (moduleDataDict array), array of applyed module
        per context.
        """
        print "Modules GET:" + request.path + ", " + parameter
        return "Modules GET:" + request.path + ", " + parameter

    def render_POST(self, requst, parameter):
        """
        await: a single moduleDataDict, a matrix of target,
        the status of active|deactive.
        """
        print "Modules POST:" + request.path + ", " + parameter
        return "Modules POST:" + request.path + ", " + parameter


    def getChild(self, path, request):
        print self.__class__.name, "Modules - ENUM - child request!", path, request
        return ModulesHandlers()

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
        print self.__class__.name, "TIP Got child request!", path, request
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
