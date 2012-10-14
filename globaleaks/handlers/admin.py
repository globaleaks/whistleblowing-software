# -*- coding: UTF-8
#
#   admin
#   *****
#
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
from globaleaks.rest import answers

from globaleaks.handlers.base import BaseHandler

class AdminNode(BaseHandler):

    # A1
    """
    Get the node main settings, update the node main settings
    """
    def get(self):
        pass

    def post(self):
        pass


class AdminContexts(BaseHandler):
    # A2
    """
    classic CURD in the 'contexts'
    """
    def get(self, context_id):
        pass

    def post(self, context_id):
        pass

    def put(self, context_id):
        pass

    def delete(self, context_id):
        pass


class AdminReceivers(BaseHandler):
    # A3
    """
    classic CURD in the 'receivers'
    """
    def get(self, context_id):
        pass

    def post(self, context_id):
        pass

    def put(self, context_id):
        pass

    def delete(self, context_id):
        pass


class AdminModules(BaseHandler):
    # A4
    """
    A limited CURD (we've not creation|delete, just update, with
    maybe a flag that /disable/ a module)
    """
    def get(self, context_id, module_id):
        pass

    def post(self, context_id, module_id):
        pass
