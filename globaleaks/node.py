# -*- coding: UTF-8
#   node
#   ****
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
from globaleaks import Processor
from globaleaks.rest import answers

class Node(Processor):
    def root_GET(*arg, **kw):
        response = {"contexts": []}
        return response
