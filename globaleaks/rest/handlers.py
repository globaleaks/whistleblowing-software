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
from globaleaks.utils.JSONhelper import *

__all__ = [ 'nodeHandler', 
                # single, P1
            'submissionHandlers', 
                # (parameter  + fixed), P2-P7
            'receiverHandlers',
                # (parameter + parameter) and (parameter + fixed), R1-R2
            'adminHandlers',
                # generic handler of /admin/ resource
            'adminContextHandler', 'adminNodeHandler', 'adminGroupHandlers', 
            'adminReceiversHandlers', 'adminModulesHandlers',
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
        resource.Resource.__init__(self)

    def render_GET(self, request, parameter):
        print "P1 GET", __name__, request.path, type(request), type(parameter)

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
Submission, GET only, /submission
P2
"""
class submissionHandlers(resource.Resource):
    def render_GET(self, request):
        print "P2 GET", request
        retjson = genericDict('render_GET_P2')
        retjson.add_string('blah_subm_ID_4324242', 'submission-ID')
        retjson.add_int(1234567890, 'creation-Time')
        return retjson.printJSON()

"""
receiverHandlers, /receiver/<uniq_Tip_$ID>/overview
R1
"""
class receiverHandlers(parameterHandler):
    path = 'overview'

    def __init__(self):
        resource.Resource.__init__(self)

    def getChild(self, path, request):
        print "receiverHandlers got child request!", path, request
        return receiverHandlers()

    def render_GET(self, request, parameter):
        """
        return the list of all the description of the available 
        notification/delivery modules configurable by the user.
        """
        print "R1 GET", __name__, request.path
        retjson = genericDict('render_GET_R2')
        retjson.add_string('TheWouldBeAListOfNotificationAndDeliveryModules', 'modules')
        return retjson.printJSON()

    def render_POST(self, request, parameter):
        print "R1 POST", __name__, request.path, "now render_GET"
        return self.render_GET(request, parameter)

    def render_PUT(self, request, parameter):
        print "R1 PUT", __name__, request.path, "now render_GET"
        return self.render_GET(request, parameter)

    def render_DELETE(self, request, parameter):
        print "R1 DELETE", __name__, request.path, "now render_GET"
        return self.render_GET(request, parameter)


"""
adminHandlers cover A1,A5
"""
class adminHandlers(resource.Resource):
    path = 'default'

    def __init__(self):
        resource.Resource.__init__(self)

    def getChild(self, path):
        print self.__class__.name, "adminHanlders got child request!", path
        return adminHandlers()

"""
NodeHandler part of adminHandlers covert, /admin/node
do not expect a parameter. handle READ and SET
A1
"""
class adminNodeHandler(parameterHandler):

    def render_GET(self, request, parameter):
        """
        return the information of the node, various blob of data
        object contained: nodeStatisticDict, nodePropertiesDict,
        contextDescription (array of), localizationDict
        """
        print "A1 GET", __name__, request.path, type(request), type(parameter)

        retjson = genericDict('render_GET_A1')
        retjson.add_string('NodeNameForTheAdmin', 'name')
        retjson.add_string('StatisticToBeXXX', 'statistics')
        retjson.add_string('SomePrivateStatsasBefore', 'private_stats')
        retjson.add_string('ConfigurableBooleanParameter', 'node_properties')
        retjson.add_string('thisIStheDescription', 'description')
        retjson.add_string('http://www.globaltest.int/whistleblowing/', 'public_site')
        retjson.add_string('nco2nfio4nioniof2n43.onion', 'hidden_service')
        retjson.add_string('/whistleblowing/', 'url_schema')
        return retjson.printJSON()

    def render_POST(self, request, parameter):
        """
        await partially the data returned by GET, and some node 
        specific configuration. return as GET with the updated
        values
        """
        print __name__, request.path, type(request), type(parameter)
        print "A1 POST", request, "render_GET"
        return self.render_GET(request, parameter)

    def getChild(self, path, request):
        print self.__class__.name, "A1 child request!", path, request
        return adminNodeHandler()


"""
ContextHandler part of adminHandlers covert /admin/contexts CURD
A2
"""
class adminContextHandler(parameterHandler):

    def render_GET(self, request, parameter):
        """
        return array of contextDescriptionDict
        """
        print "A2 GET:" + request.path + ", " + parameter

        context1 = contextDescriptionDict('c1_render_GET_A2')
        context1.name('context_1_Name')
        context1.description('context_1_description')
        context1.style('context_1_style')
        context1.creation_date(123450)
        context1.update_date(123456)

        context2 = contextDescriptionDict('c2_render_GET_A2')
        context2.name('context_2_Name')
        context2.description('context_2_description')
        context2.style('context_2_style')
        context2.creation_date(444440)
        context2.update_date(444446)

        retjson = genericDict('context_GET_A2_array')
        retjson.add_array([ context1.printJSON(), context2.printJSON() ], 'contexts')

        return retjson.printJSON()

    def render_POST(self, request, parameter):
        """
        check 'create' or 'delete' and wait a
        contextDescriptionDict to be updated
        return as get or errors
        """
        print "A2 POST:" + request.path + ", " + parameter
        receivedjson = genericDict('received_A2_POST')
        print type(request)
        print request
        # check delete - create
        if isinstance(request, dict):
            receivedjson.push_fields(request)
            print "received JSON imported by RestJSONwrapper: ",
            print receivedjson.printJSON()
        return self.render_GET(request, parameter)

    def render_PUT(self, request, parameter):
        """
        await a context to add, and assign an ID
        return as get or errors
        """
        print "A2 PUT:" + request.path + ", " + parameter
        receivedjson = genericDict('received_A2_PUT')
        print type(request)
        print request
        if isinstance(request, dict):
            receivedjson.push_fields(request)
            print "received JSON imported by RestJSONwrapper: ",
            print receivedjson.printJSON()
        return self.render_GET(request, parameter)


    def render_DELETE(self, request, parameter):
        """
        await a context to delete, check if exists
        return as get or errors
        """
        print "A2 DELETE:" + request.path + ", " + parameter
        receivedjson = genericDict('received_A2_DELETE')
        print type(request)
        print request
        if isinstance(request, dict):
            receivedjson.push_fields(request)
            print "received JSON imported by RestJSONwrapper: ",
            print receivedjson.printJSON()
        return self.render_GET(request, parameter)

    def getChild(self, path, request):
        print self.__class__.name, "A2 child request!", path, request
        return adminContextHandler()


"""
GroupHandler part of adminHandlers covert 
/admin/groups/<context_$ID> CURD
# A3
"""
class adminGroupHandlers(parameterHandler):

    def render_GET(self, request, parameter):
        """
        return two Arrays, groupDescriptionDict
        and modules_available (moduleDataDict)
        """
        print "A3 GET:" + request.path + ", " + parameter

        group1 = groupDescriptionDict('group_A3_elem1')

        group1.group_name('group_1_name')
        group1.description('new description for group 1')
        group1.spoken_language('array-1 TBD')
        group1.group_tags('tag11, targ12, tag13')

        group2 = groupDescriptionDict('group_A3_elem2')

        group2.group_name('group_2_name')
        group2.description('new description for group 2')
        group2.spoken_language('array-2 TBD')
        group2.group_tags('tag21, targ22, tag23')

        retjson = genericDict('render_GET_A3')
        retjson.add_array([ group1.printJSON(), group2.printJSON()], 'groups')
        return retjson.printJSON()

    def render_POST(self, request, parameter):
        """
        check 'create' or 'delete' and wait a
        groupDescriptionDict to be updated
        return as get
        """
        print "A3 POST:" + request.path + ", " + parameter + "return as GET"

        receivedjson = genericDict('received_A3_POST')
        print type(request)
        print request
        if isinstance(request, dict):
            receivedjson.push_fields(request)
            print "received JSON imported by RestJSONwrapper: ",
            print receivedjson.printJSON()

        return self.render_GET(request, parameter)

    def render_PUT(self, request, parameter):
        """
        await a groupDescriptionDict, verify, create ID
        return as get
        """
        print "A3 PUT:" + request.path + ", " + parameter

        receivedjson = genericDict('received_A3_PUT')
        print type(request)
        print request
        if isinstance(request, dict):
            receivedjson.push_fields(request)
            print "received JSON imported by RestJSONwrapper: ",
            print receivedjson.printJSON()

        return self.render_GET(request, parameter)


    def render_DELETE(self, request, parameter):
        """
        await a valid groupDescriptionDict,
        return as get or error if ID is missing
        """
        print "A3 DELETE:" + request.path + ", " + parameter

        receivedjson = genericDict('received_A3_DELETE')
        print type(request)
        print request
        if isinstance(request, dict):
            receivedjson.push_fields(request)
            print "received JSON imported by RestJSONwrapper: ",
            print receivedjson.printJSON()

        return self.render_GET(request, parameter)

    def getChild(self, path, request):
        print self.__class__.name, "A3 child request!", path, request
        return adminGroupHandlers()


"""
ReceiverHandlers part of adminHandlers covers
/admin/receivers/<group_$ID> A4
"""
class adminReceiversHandlers(parameterHandler):
    def render_GET(self, request, parameter):
        """
        return Array of receiverDescriptionDict,
        """
        print "A4 GET:" + request.path + ", " + parameter

        receiver1= receiverDescriptionDict('receiver_A4_R1')
        receiver1.name('receiverName1-A4')
        receiver1.description('blah blah-1')
        receiver1.contact_data('configured-email: receiver1@dm.tld')
        receiver1.module_id('email_receiver_module_handler')

        # Change name of "_data" in "_message" ? 
        # this is a message appearing as flavor text, 
        # explaining what's the working status, if detected.
        receiver1.module_dependent_data('yor email has been verified')

        receiver2= receiverDescriptionDict('receiver_A4_R2')
        receiver2.name('receiverName2')
        receiver2.description('blah blah-2')
        receiver2.contact_data('configured-email: receiver2@dm.tld')
        receiver2.module_id('email_receiver_module_handler')

        retjson = genericDict('render_GET_A4')
        retjson.add_array([ receiver1.printJSON(), receiver2.printJSON()], 'receivers')
        return retjson.printJSON()


    def render_POST(self, request, parameter):
        """
        check 'create' or 'delete' and wait a
        receiverDescriptionDict to be updated
        return as get
        """
        print "A4 POST:" + request.path + ", " + parameter
        receivedjson = genericDict('received_A4_POST')
        print type(request)
        print request
        if isinstance(request, dict):
            receivedjson.push_fields(request)
            print "received JSON imported by RestJSONwrapper: ",
            print receivedjson.printJSON()
        return self.render_GET(request, parameter)

    def render_PUT(self, request, parameter):
        """
        await a receiverDescriptionDict, verify, create
        return as get
        """
        print "A4 PUT:" + request.path + ", " + parameter
        receivedjson = genericDict('received_A4_PUT')
        print type(request)
        print request
        if isinstance(request, dict):
            receivedjson.push_fields(request)
            print "received JSON imported by RestJSONwrapper: ",
            print receivedjson.printJSON()
        return self.render_GET(request, parameter)


    def render_DELETE(self, request, parameter):
        """
        await a valid groupDescriptionDict,
        return as get or error if ID is missing
        """
        print "A4 DELETE:" + request.path + ", " + parameter
        receivedjson = genericDict('received_A4_DELETE')
        print type(request)
        print request
        if isinstance(request, dict):
            receivedjson.push_fields(request)
            print "received JSON imported by RestJSONwrapper: ",
            print receivedjson.printJSON()
        return self.render_GET(request, parameter)

    def getChild(self, path, request):
        print self.__class__.name, "A4 child request!", path, request
        return adminReceiversHandlers()

"""
ModulesHandlers handle /admin/modules/<string module_type> A5
"""
class adminModulesHandlers(parameterHandler):
    def render_GET(self, request, parameter):
        """
        return the list of module present in a node,
        (moduleDataDict array), inside of them there are
        the 'actived' field
        """
        print "A5 GET:" + request.path + ", " + parameter

        mod1 = moduleDataDict('module_GET_A5_1', 'Delivery1')
        mod1.active(True)
        mod1.name('Module for good 1')
        mod1.description("I'm the desc of module Delivery active 1")
        mod1.admin_options('some dummy option for admin 1')
        mod1.user_options('some dummy option for user 1')
        mod1.service_message('some spare data of module ONE')

        mod2 = moduleDataDict('module_GET_A5_2', 'Delivery2')
        mod2.active(False)
        mod2.name('Module for bad 2')
        mod2.description("I'm the desc of module Delivery inactive 2")
        mod2.admin_options('some dummy option for admin 2')
        mod2.service_message('blah blah - thankyou for chooing bad2')

        retjson = genericDict('render_GET_A5')
        retjson.add_array([ mod1.printJSON(), mod2.printJSON()], 'modules')
        retjson.add_string("TODO TODO TODO", 'group_matrix')
        return retjson.printJSON()

    def render_POST(self, request, parameter):
        """
        check 'create' or 'delete' and wait a
        moduleDataDict to be updated
        return as get
        inside the moduleDataDict would find also the 'active' flag
        inside the group_matrix follow the application table of 
        all the module and the groups.
        """
        print "A5 POST:" + request.path + ", " + parameter, "render_GET"
        return self.render_GET(request, parameter)


    def render_PUT(self, request, parameter):
        """
        put a new moduleDataDict in db storage and update the group_matrix
        """
        print "A5 PUT:" + request.path + ", " + parameter
        return self.render_GET(request, parameter)

    def render_DELETE(self, request, parameter):
        """
        delete a module configuration (remain returned in GET with the
        module not configured neither active, and flush all occurrencies
        in the group_matrix)
        group_matrix ignored
        """
        print "A5 DELETE:" + request.path + ", " + parameter
        return self.render_GET(request, parameter)

    def getChild(self, path, request):
        print self.__class__.name, "A5 child request!", path, request
        return adminModulesHandlers()


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
