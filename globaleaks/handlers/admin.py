# -*- coding: UTF-8
#
#   admin
#   *****
#
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
from globaleaks.handlers.base import BaseHandler
from globaleaks.models import node, context, receiver
from globaleaks.utils import log
from cyclone.web import asynchronous
from twisted.internet.defer import inlineCallbacks
import json

class AdminNode(BaseHandler):
    """
    A1
    Get the node main settings, update the node main settings, it works in a single static
    table, in models/admin.py

    Since this point start the administration chain:
    . admin GET A1 (full context description with private infos)
      . admin works in A2 (context management, having the context_gus list)
      . admin works in A3 (receiver management, having the receiver_gus list)
    """

    @asynchronous
    @inlineCallbacks
    def get(self, *uriargs):
        """
        The Get interface is thinked as first blob of data able to present the node,
        therefore not all the information are specific of this resource (like
        contexts description or statististics), but for reduce the amount of request
        performed by the client, has been collapsed into.

        Returns a json object containing all the information of the node.
        * Response:
            Status Code: 200 (OK)
            {
              'name': 'string',
              'admin_statistics': '$adminStatisticsDict',
              'public_stats': '$publicStatisticsDict,
              'node_properties': '$nodePropertiesDict',
              'contexts': [ '$contextDescriptionDict', { }, ],
              'node_description': '$localizationDict',
              'public_site': 'string',
              'hidden_service': 'string',
              'url_schema': 'string'
             }

        not yet implemented: admin_stats (stats need to be moved in contexts)
        node_properties: should not be separate array
        url_schema: no more needed ?
        stats_delta couple.
        """

        log.debug("[D] %s %s " % (__file__, __name__), "Class Admin Node", "GET")

        context_iface = context.Context()
        context_description_dicts = yield context_iface.admin_get_all()

        node_info = node.Node()
        node_description_dicts = yield node_info.get_admin_info()

        # it's obviously a madness that need to be solved
        node_description_dicts.update({"contexts": context_description_dicts})

        self.set_status(200)
        self.write(node_description_dicts)
        self.finish()

    @asynchronous
    @inlineCallbacks
    def post(self, *uriargs):
        """
        Changes the node public node configuration settings
        * Request:
            {
              'name': 'string',
              'admin_stats_delta', 'int',
              'public_stats_delta', 'int',
              'description': '$localizationDict',
              'public_site': 'string',
              'hidden_service': 'string',
             }

        The two "_delta" variables, mean the minutes interval for collect statistics,
        because the stats are collection of the node status made over periodic time,

        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminNode", "POST")

        request = json.loads(self.request.body)

        if not request:
            # holy fucking sick atheist god
            # no validation at the moment.
            self.write(__file__)
            self.write('error message to be managed using the appropriate format')
            self.finish()

        node_info = node.Node()
        yield node_info.configure_node(request)

        # return value as GET
        yield self.get()


class AdminContexts(BaseHandler):
    """
    A2: classic CRUD in the 'contexts', not all expect a context_gus in the URL,
    in example PUT need context_gus because Cyclone regexp expect them, but
    do not require a valid data because is generated when the resource is PUT-ted
    """
    log.debug("[D] %s %s " % (__file__, __name__), "Class AdminContexts", "BaseHandler", BaseHandler)

    @asynchronous
    @inlineCallbacks
    def get(self, context_gus, *uriargs):
        """
        :GET
          * Response
            Return the requested contexts, described with:
            contextDescriptionDict
               {
                "context_gus": "context_gus"
                "name": "string"
                "context_description": "string"
                "creation_date": "time"
                "update_date": "time"
                "fields": [ formFieldsDict ]
                "SelectableReceiver": "bool"
                "receivers": [ receiverDescriptionDict ]
                "escalation_threshold": "int"
                "LanguageSupported": [ "string" ]
               }
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminContexts", "GET")

        context_iface = context.Context()

        try:
            context_description = yield context_iface.admin_get_single(context_gus)

            self.set_status(200)
            self.write(context_description)

        except context.InvalidContext, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()

    @asynchronous
    @inlineCallbacks
    def post(self, context_gus, *uriargs):
        """
        Update a previously created context
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminContexts", "POST")

        request = json.loads(self.request.body)

        if not request:
            # holy fucking sick atheist god
            # no validation at the moment.
            self.write(__file__)
            self.write('error message to be managed using the appropriate format')
            self.finish()

        context_iface = context.Context()

        try:
            yield context_iface.update(context_gus, request)
            yield self.get(context_gus)

            self.set_status(200)

        except context.InvalidContext, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


    @asynchronous
    @inlineCallbacks
    def put(self, context_gus, *uriargs):
        """
        create a new context and return as GET
        :PUT
         * Request {
            "context_gus": empty or missing
            [...]
           }
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminContexts", "PUT")
        request = json.loads(self.request.body)

        if not request:
            # holy fucking sick atheist god
            # no validation at the moment.
            self.write(__file__)
            self.write('error message to be managed using the appropriate format')
            self.finish()

        context_iface = context.Context()

        # XXX detect which operation can fail, and eventually make an appropriate
        # exception, with the logic used in self.post
        new_context_gus = yield context_iface.new(request)

        # return value as GET
        yield self.get(new_context_gus)


    @asynchronous
    @inlineCallbacks
    def delete(self, context_gus, *uriargs):
        """
        Expect just a context_gus, do not check in the body request
        * Request:
            DELETE /admin/context/<context_gus>

        * Response:
            200 if Context exists when requested
            XXX if Context is invalid
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminContext", "DELETE", context_gus)


        context_iface = context.Context()

        # XXX just a litle consideration: if a context has some tip, jobs, whatever
        # in queue, maybe the client ask a sort of "are you really sure ?"
        # this operation is not related to this REST DELETE, but perhaps in the
        # administrative view of the contexts, also the presence|absence|description
        # of the queued operations, would be useful.

        # This DELETE operation, its fucking permanant, and kills all the Tip related
        # to the context. (not the receivers: they can be possesed also by other context,
        # but the tarGET context is DELETEd also in the receiver reference)

        try:
            yield context_iface.delete_context(context_gus)
            self.set_status(200)

        except context.InvalidContext, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()



class AdminReceivers(BaseHandler):
    """
    A3: AdminReceivers: classic CRUD in a 'receiver' resource
    A receiver can stay in more than one context, then is expected in POST/PUT
    operations a list of tarGET contexts is passed. Operation here, mostly are
    handled by models/receiver.py, and act on the administrative side of the
    receiver. a receiver performing operation in their profile, has an API
    implemented in handlers.receiver
    """

    @asynchronous
    @inlineCallbacks
    def get(self, receiver_gus, *uriargs):

        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminReceivers", "GET", receiver_gus)

        receiver_iface = receiver.Receiver()

        try:
            receiver_description = yield receiver_iface.admin_get_single(receiver_gus)

            self.set_status(200)
            self.write(receiver_description)

        except context.InvalidContext, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except receiver.InvalidReceiver, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


    @asynchronous
    @inlineCallbacks
    def post(self, receiver_gus, *uriargs):
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminReceivers", "POST", receiver_gus)

        request = json.loads(self.request.body)

        if not request:
            # holy fucking sick atheist god
            # no validation at the moment.

            self.write(__file__)
            self.write('error message to be managed using the appropriate format')
            self.set_status(400)
            self.finish()

        receiver_iface = receiver.Receiver()

        try:
            yield receiver_iface.admin_update(receiver_gus, request)

            yield self.get(receiver_gus)

        except context.InvalidContext:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})
            self.finish()

        except receiver.InvalidReceiver, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})
            self.finish()



    @asynchronous
    @inlineCallbacks
    def put(self, receiver_gus, *uriargs):
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminReceivers", "PUT", receiver_gus)

        request = json.loads(self.request.body)

        if not request:
            # holy fucking sick atheist god
            # no validation at the moment.
            self.write(__file__)
            self.write('error message to be managed using the appropriate format')
            self.finish()

        receiver_iface = receiver.Receiver()
        new_receiver_gus = yield receiver_iface.new(request)

        # return value as GET of the new receiver
        yield self.get(new_receiver_gus)


    @asynchronous
    @inlineCallbacks
    def delete(self, receiver_gus, *uriargs):
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminReceivers", "DELETE", receiver_gus)

        receiver_iface = receiver.Receiver()

        try:
            yield receiver_iface.receiver_delete(receiver_gus)
            self.set_status(200)

        except context.InvalidContext, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except receiver.InvalidReceiver, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()

class AdminModules(BaseHandler):
    log.debug("[D] %s %s " % (__file__, __name__), "Class AdminModules", "BaseHandler", BaseHandler)
    # A4
    """
    A limited CRUD (we've not creation|DELETE, just update, with
    maybe a flag that /disable/ a module)
    """
    def get(self, module_gus, *uriargs):
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminModules", "GET")
        pass

    def post(self, module_gus, *uriargs):
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminModules", "POST")
        pass
