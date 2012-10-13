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
from globaleaks.utils.dummy import dummy_answers as dummy

from globaleaks.handlers.base import BaseHandler

class AdminNode(BaseHandler):

    # A1
    """
    Get the node main settings, update the node main settings
    """
    def get(self, *arg, **kw):

        ret = answers.nodeMainSettings()

        dummy.ADMIN_NODE_GET(ret)
        return ret.unroll()

    def post(self, *arg, **kw):
        return self.node_GET(arg, kw)


class AdminContexts(BaseHandler):
    # A2
    """
    classic CURD in the 'contexts'
    """
    def get(self, context_id):

        ret = answers.adminContextsCURD()

        dummy.ADMIN_CONTEXTS_GET(ret)

        return ret.unroll()

    def post(self, context_id):
        return self.get(context_id)

    def put(self, context_id):
        return self.get(context_id)

    def delete(self, context_id):
        return self.get(context_id)


class AdminReceivers(BaseHandler):
    # A3
    """
    classic CURD in the 'receivers'
    """
    def get(self, context_id):

        ret = answers.adminReceiverCURD()

        dummy.ADMIN_RECEIVERS_GET(ret)

        return ret.unroll()

    def post(self, context_id):
        return self.get(context_id)

    def put(self, context_id):
        return self.get(context_id)

    def delete(self, context_id):
        return self.get(context_id)


class AdminModules(BaseHandler):
    # A4
    """
    A limited CURD (we've not creation|delete, just update, with
    maybe a flag that /disable/ a module)
    """
    def get(self, context_id, module_id):

        ret = answers.adminModulesUR()

        dummy.ADMIN_MODULES_GET(ret)

        return ret

    def post(self, context_id, module_id):
        return self.get(context_id, module_id)

