# -*- coding: UTF-8
#   node
#   ****
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#

from twisted.internet.defer import inlineCallbacks

from globaleaks.utils import log
from globaleaks.models import node, admin
from globaleaks.handlers.base import BaseHandler
from cyclone.web import asynchronous

class Node(BaseHandler):
    """
    U1
    Returns information on the GlobaLeaks node. This includes submission
    paramters and how information should be presented by the client side
    application.

    Follow the resource describing Node (uniq instance, accessible to all)
    """

    @asynchronous
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Returns a json object containing all the information of the node.
        * Response:
            Status Code: 200 (OK)
            {
              'name': 'string',
              'statistics': '$nodeStatisticsDict',
              'node_properties': '$nodePropertiesDict',
              'contexts': [ '$contextDescriptionDict', { }, ],
              'description': '$localizationDict',
              'public_site': 'string',
              'hidden_service': 'string',
              'url_schema': 'string'
             }

        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class Node", "get", uriargs)

        """
        try:
        """
        nodeinfo = node.Node()
        node_description_dicts = yield nodeinfo.get_public_info()
        """
        except NodeNotFoundError, e:
            log.err("Fatal ? node not found!")
            print e.error_message, dir(e)
            self.write('errormessage')
            self.finish()
        """

        context = admin.Context()
        context_description_dicts = yield context.get_all_contexts()

        node_description_dicts.update({"contexts": context_description_dicts})

        self.write(node_description_dicts)
        self.finish()
