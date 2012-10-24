# -*- coding: UTF-8
#   node
#   ****
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#

from twisted.internet.defer import inlineCallbacks

from globaleaks.utils import log
from globaleaks import models

from cyclone.web import RequestHandler, asynchronous

class Node(RequestHandler):
    """
    U1
    Returns information on the GlobaLeaks node. This includes submission
    paramters and how information should be presented by the client side
    application.

    Follow the resource describing Node (uniq instance, accessible to all)
    """
    log.debug("[D] %s %s " % (__file__, __name__), "Class Node", "RequestHandler", RequestHandler)

    @asynchronous
    @inlineCallbacks
    def get(self):
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
        log.debug("[D] %s %s " % (__file__, __name__), "Class Node", "get")

        from globaleaks.messages import dummy

        context = models.admin.Context()
        context_description_dicts = yield context.list_description_dicts()

        print "debug thafucq ", context_description_dicts
        node = models.node.Node()
        node_description_dicts = yield node.get_public_info()

        print "dabeg thyfacq ", node_description_dicts

        # this is madness ?
        response = {"contexts": context_description_dicts,
            # THIS IS SPARTAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
                    "public_statistics": dummy.base.publicStatisticsDict,
                    "node_properties": dummy.base.nodePropertiesDict,
                    "public_site": "http://www.fuffa.org/",
                    "hidden_service": "cnwoecowiecnirnio23rn23io.onion",
                    "url_schema": "/",
                    "name": "don't track us: AUTOVELOX"}
        self.write(response)
        self.finish()
