# -*- coding: UTF-8
#   node
#   ****
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#

from twisted.internet.defer import inlineCallbacks
from globaleaks.utils import log
from globaleaks.handlers.base import BaseHandler
from cyclone.web import asynchronous

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
        Response: publicNodeDesc
        Errors: NodeNotFoundError
        """

        from globaleaks.models.node import Node, NodeNotFoundError
        from globaleaks.models.context import Context

        log.debug("[D] %s %s " % (__file__, __name__), "Class Node", "get", uriargs)

        try:
            nodeinfo = Node()
            node_description_dicts = yield nodeinfo.get_public_info()

            context_view = Context()
            public_context_view = yield context_view.public_get_all()
            node_description_dicts.update({"contexts": public_context_view})

            # XXX this is an aggregate answer, need to be output-validated here

            self.write(node_description_dicts)

        except NodeNotFoundError, e:

            self._status_code = e.http_status
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


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
        Parameters: TODO
        Response: publicStatsList
        Errors: StatsNotCollectedError

        This interface return the collected statistics for the public audience.
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class StatsAvailable", "get", uriargs)
        pass
