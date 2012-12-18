# -*- coding: UTF-8
#   node
#   ****
#
# Implementation of classes handling the HTTP request to /node, public
# exposed API.

from twisted.internet.defer import inlineCallbacks
from globaleaks.utils import log
from globaleaks.handlers.base import BaseHandler
from cyclone.web import asynchronous
from globaleaks.models.node import Node
from globaleaks.models.context import Context
from globaleaks.models.receiver import Receiver
from globaleaks.rest.errors import NodeNotFound
import json

class InfoCollection(BaseHandler):
    """
    U1
    Returns information on the GlobaLeaks node. This includes submission
    parameters (contexts description, fields, public receiver list).
    Contains System-wide properties.
    """

    @asynchronous
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: publicNodeDesc
        Errors: NodeNotFound
        """

        log.debug("[D] %s %s " % (__file__, __name__), "Class Node", "get", uriargs)

        try:
            nodeinfo = Node()
            node_description_dicts = yield nodeinfo.get_public_info()

            self.write(node_description_dicts)

        except NodeNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()

# U2 Submission create
# U3 Submission update/status/delete
# U4 Files

class StatsCollection(BaseHandler):
    """
    U5
    Interface for the public statistics, configured between the Node settings and the
    Contexts settings
    """

    @asynchronous
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: publicStatsList
        Errors: StatsNotCollectedError

        This interface return the collected statistics for the public audience.
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class StatsAvailable", "get", uriargs)
        pass

class ContextsCollection(BaseHandler):
    """
    U6
    Return the public list of contexts, those information are shown in client
    and would be memorized in a third party indexer service. This is way some dates
    are returned within.
    """

    @asynchronous
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: publicContextList
        Errors: None
        """

        try:
            context_view = Context()
            public_context_view = yield context_view.public_get_all()

            self.set_status(200)
            self.write(json.dumps(public_context_view))
            # TODO output filter + json

        except KeyError: # TODO there are some error that can be returned ?

            self.set_status(444)
            self.write({'error_message': 'do not exist but TODO', 'error_code' : 12345})

        self.finish()


class ReceiversCollection(BaseHandler):
    """
    U7
    Return the description of all the receiver visible from the outside. A receiver is associated
    to one or more context, and is present in the "first tier" if a multi level review is configured.
    """

    @asynchronous
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: publicReceiverList
        Errors: None
        """

        try:
            receiver_view = Receiver()
            public_receiver_view = yield receiver_view.public_get_all()

            self.set_status(200)
            self.write(json.dumps(public_receiver_view))
            # TODO output filter + json

        except KeyError: # TODO there are some error that can be returned ?

            self.set_status(444)
            self.write({'error_message': 'do not exist but TODO', 'error_code' : 12345})

        self.finish()




