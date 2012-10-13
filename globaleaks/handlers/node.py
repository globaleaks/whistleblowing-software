# -*- coding: UTF-8
#   node
#   ****
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
from globaleaks.rest import answers
from globaleaks import models

from cyclone.web import RequestHandler

def create_node(contextDict):
    context = models.base.Context()
    context.name = contextDict['name']
    context.description = contextDict['description']
    context.fields = contextDict['fields']
    context.selectable_receiver = contextDict['selectable_receiver']
    context.escalation_threshold = contextDict['escalation_threshold']
    context.languages_supported = contextDict['languages_supported']

class Node(RequestHandler):
    def get(self, *arg, **kw):
        from globaleaks.messages.dummy import answers
        response = answers.nodeRootGet
        self.write(response)
        print "Doing node!"
