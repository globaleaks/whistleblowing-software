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
from globaleaks.rest.errors import NodeNotFound

class InfoAvailable(BaseHandler):
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


            # Remind: this is no more an aggregate answer, a client need to perform
            # a GET /contexts to retrive list of contexts.

            self.write(node_description_dicts)

        except NodeNotFound, e:

            self._status_code = e.http_status
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


class ContextsAvailable(BaseHandler):
    """
    U5
    """

    @asynchronous
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response:
        Errors:
        """

        log.debug("[D] %s %s " % (__file__, __name__), "Class Node", "get", uriargs)

        try:
            context_view = Context()
            public_context_view = yield context_view.public_get_all()
            node_description_dicts.update({"contexts": public_context_view})

            # todo output filter
        except KeyError: # TODO the error returned by the in

class ReceiversAvailable(BaseHandler):
    """
    U6
    """

    @asynchronous
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response:
        Errors:
        """


class StatsAvailable(BaseHandler):
    """
    U4
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
