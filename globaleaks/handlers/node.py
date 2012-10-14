# -*- coding: UTF-8
#   node
#   ****
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#

from twisted.internet.defer import inlineCallbacks

from globaleaks.rest import answers
from globaleaks import models

from cyclone.web import RequestHandler, asynchronous

def create_node(context_dict):
    context = models.admin.Context()
    context.name = context_dict['name']
    context.description = context_dict['description']
    context.fields = context_dict['fields']
    context.selectable_receiver = context_dict['selectable_receiver']
    context.escalation_threshold = context_dict['escalation_threshold']
    context.languages_supported = context_dict['languages_supported']

class Node(RequestHandler):

    @asynchronous
    @inlineCallbacks
    def get(self):
        from globaleaks.messages import dummy

        context = models.admin.Context()
        context_description_dicts = yield context.list_description_dicts()
        response = {"contexts": context_description_dicts,
                    "public_statistics": dummy.base.publicStatisticsDict,
                    "node_properties": dummy.base.nodePropertiesDict,
                    "public_site": "http://www.fuffa.org/",
                    "hidden_service": "cnwoecowiecnirnio23rn23io.onion",
                    "url_schema": "/",
                    "name": "don't track us: AUTOVELOX"}
        self.write(response)
        self.finish()
