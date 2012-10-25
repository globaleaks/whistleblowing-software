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
from globaleaks.models import node, admin, context
from globaleaks.utils import log
from cyclone.web import asynchronous
from twisted.internet.defer import inlineCallbacks
import json

class AdminNode(BaseHandler):
    """
    A1
    Get the node main settings, update the node main settings, it works in a single static
    table, in models/admin.py
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

        log.debug("[D] %s %s " % (__file__, __name__), "Class Admin Node", "get")

        context = admin.Context()
        context_description_dicts = yield context.get_all_contexts()

        node_info = node.Node()
        node_description_dicts = yield node_info.get_admin_info()

        # it's obviously a madness that need to be solved
        node_description_dicts.update({"contexts": context_description_dicts})

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
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminNode", "post")

        request = json.loads(self.request.body)

        if not request:
            # holy fucking sick atheist god
            # no validation at the moment.
            self.write(__file__)
            self.write('error message to be managed using the appropriate format')
            self.finish()

        node_info = node.Node()
        yield node_info.configure_node(request)

        # return value as get
        yield self.get()


class AdminContexts(BaseHandler):
    """
    classic CRUD in the 'contexts', not all expect a context_gus in the URL,
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
                "escalation_treshold": "int"
                "LanguageSupported": [ "string" ]
               }
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminContexts", "GET")

        context_iface = admin.Context()

        try:
            context_description = yield context_iface.get_single_context(context_gus)

            self._status_code = 200
            self.write(context_description)

        except admin.InvalidContext, e:

            self._status_code = e.http_status
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

        context_iface = admin.Context()
        yield context_iface.update(context_gus, request)

        # return value as get
        yield self.get(context_gus)

    @asynchronous
    @inlineCallbacks
    def put(self, context_gus, *uriargs):
        """
        create a new context and return as get
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

        context_iface = admin.Context()
        new_context_gus = yield context_iface.new(request)

        # return value as get
        yield self.get(new_context_gus)


    @asynchronous
    @inlineCallbacks
    def delete(self, context_gus, *uriargs):
        """
        Expect just a context_gus, do not check in the body request
        (at the moment, is specify in a different way, to avoid conflict
        """

        context_iface = admin.Context()

        try:
            yield context_iface.delete_context(context_gus)
            self._status_code = 200

        except admin.InvalidContext, e:

            self._status_code = e.http_status
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()



class AdminReceivers(BaseHandler):
    log.debug("[D] %s %s " % (__file__, __name__), "Class AdminReceivers", "BaseHandler", BaseHandler)
    # A3
    """
    classic CRUD in the 'receivers'
    """
    def get(self, context_id):
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminReceivers", "get")
        pass

    def post(self, context_id):
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminReceivers", "post")
        pass

    def put(self, context_id):
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminReceivers", "put")
        pass

    def delete(self, context_id):
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminReceivers", "delete")
        pass


class AdminModules(BaseHandler):
    log.debug("[D] %s %s " % (__file__, __name__), "Class AdminModules", "BaseHandler", BaseHandler)
    # A4
    """
    A limited CRUD (we've not creation|delete, just update, with
    maybe a flag that /disable/ a module)
    """
    def get(self, context_id, module_id):
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminModules", "get")
        pass

    def post(self, context_id, module_id):
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminModules", "post")
        pass
